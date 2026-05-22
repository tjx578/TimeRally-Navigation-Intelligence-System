/**
 * Photo OCR intake feature.
 *
 * Mengkonversi File browser menjadi payload base64 dan mengirim ke
 * /v1/rally/photo-ocr.
 */

import { rallyApi, type PhotoOcrResponse } from "../../lib/api/rallyApi";

const OCR_IMAGE_MAX_EDGE_PX = 2200;
const OCR_IMAGE_TARGET_BYTES = 8 * 1024 * 1024;
const OCR_IMAGE_VARIANTS = [
  { maxEdgePx: 2200, quality: 0.82 },
  { maxEdgePx: 2000, quality: 0.78 },
  { maxEdgePx: 1800, quality: 0.75 },
  { maxEdgePx: 1600, quality: 0.72 }
] as const;

type PreparedOcrImage = {
  blob: Blob;
  filename: string;
  mimeType: string;
};

export async function fileToBase64(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // strip "data:image/...;base64,"
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function loadBrowserImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`${file.name}: foto tidak bisa dibaca oleh browser untuk kompresi.`));
    };
    image.src = url;
  });
}

function scaledDimensions(width: number, height: number, maxEdgePx: number) {
  const largestEdge = Math.max(width, height);
  if (largestEdge <= maxEdgePx) {
    return { width, height };
  }

  const scale = maxEdgePx / largestEdge;
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale))
  };
}

function canvasToJpegBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Browser gagal mengompresi foto soal."));
          return;
        }
        resolve(blob);
      },
      "image/jpeg",
      quality
    );
  });
}

async function renderCompressedJpeg(
  image: HTMLImageElement,
  maxEdgePx: number,
  quality: number
): Promise<Blob> {
  const sourceWidth = image.naturalWidth || image.width;
  const sourceHeight = image.naturalHeight || image.height;
  const size = scaledDimensions(sourceWidth, sourceHeight, maxEdgePx);
  const canvas = document.createElement("canvas");
  canvas.width = size.width;
  canvas.height = size.height;

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Browser tidak bisa menyiapkan kanvas kompresi foto.");
  }

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, size.width, size.height);
  ctx.drawImage(image, 0, 0, size.width, size.height);
  return canvasToJpegBlob(canvas, quality);
}

function canUseOriginalFile(file: File, image: HTMLImageElement) {
  const isUploadFriendlyType = file.type === "image/jpeg" || file.type === "image/webp";
  const largestEdge = Math.max(
    image.naturalWidth || image.width,
    image.naturalHeight || image.height
  );
  return (
    isUploadFriendlyType &&
    file.size <= OCR_IMAGE_TARGET_BYTES &&
    largestEdge <= OCR_IMAGE_MAX_EDGE_PX
  );
}

async function prepareImageForOcr(file: File): Promise<PreparedOcrImage> {
  const image = await loadBrowserImage(file);
  if (canUseOriginalFile(file, image)) {
    return {
      blob: file,
      filename: file.name,
      mimeType: file.type
    };
  }

  let smallestBlob: Blob | null = null;
  for (const variant of OCR_IMAGE_VARIANTS) {
    const blob = await renderCompressedJpeg(image, variant.maxEdgePx, variant.quality);
    if (!smallestBlob || blob.size < smallestBlob.size) {
      smallestBlob = blob;
    }
    if (blob.size <= OCR_IMAGE_TARGET_BYTES) {
      return {
        blob,
        filename: file.name,
        mimeType: blob.type
      };
    }
  }

  if (!smallestBlob || smallestBlob.size > OCR_IMAGE_TARGET_BYTES) {
    throw new Error(
      `${file.name}: foto masih terlalu besar setelah kompresi. Crop atau turunkan resolusi lalu upload ulang.`
    );
  }

  return {
    blob: smallestBlob,
    filename: file.name,
    mimeType: smallestBlob.type
  };
}

export interface QuestionPhotoUpload {
  filename: string;
  mime_type?: string;
  image_base64: string;
}

export async function preparePayload(files: File[]): Promise<QuestionPhotoUpload[]> {
  const out: QuestionPhotoUpload[] = [];
  for (const f of files) {
    const image = await prepareImageForOcr(f);
    out.push({
      filename: image.filename,
      mime_type: image.mimeType || undefined,
      image_base64: await fileToBase64(image.blob)
    });
  }
  return out;
}

export async function submitPhotos(files: File[]): Promise<PhotoOcrResponse> {
  const photos = await preparePayload(files);
  return rallyApi.photoOcr({ photos, auto_parse: true, auto_map_subtrayek: true });
}
