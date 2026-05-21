/**
 * Photo OCR intake feature.
 *
 * Mengkonversi File browser menjadi payload base64 dan mengirim ke
 * /v1/rally/photo-ocr.
 */

import { rallyApi, type PhotoOcrResponse } from "../../lib/api/rallyApi";

export async function fileToBase64(file: File): Promise<string> {
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

export interface QuestionPhotoUpload {
  filename: string;
  mime_type?: string;
  image_base64: string;
}

export async function preparePayload(files: File[]): Promise<QuestionPhotoUpload[]> {
  const out: QuestionPhotoUpload[] = [];
  for (const f of files) {
    out.push({
      filename: f.name,
      mime_type: f.type || undefined,
      image_base64: await fileToBase64(f),
    });
  }
  return out;
}

export async function submitPhotos(files: File[]): Promise<PhotoOcrResponse> {
  const photos = await preparePayload(files);
  return rallyApi.photoOcr({ photos, auto_parse: true, auto_map_subtrayek: true });
}
