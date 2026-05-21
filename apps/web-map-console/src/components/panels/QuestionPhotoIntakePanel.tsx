import { Camera, FileImage, ScanText } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { submitPhotos } from "../../features/photo-ocr-intake";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

type LocalPhoto = {
  fileName: string;
  previewUrl: string;
};

export function QuestionPhotoIntakePanel() {
  const photoOcr = useRallyWorkspaceStore((state) => state.photoOcr);
  const processQuestionPhotos = useRallyWorkspaceStore((state) => state.processQuestionPhotos);
  const setPhotoOcrResult = useRallyWorkspaceStore((state) => state.setPhotoOcrResult);
  const uploadRef = useRef<HTMLInputElement | null>(null);
  const cameraRef = useRef<HTMLInputElement | null>(null);
  const [localPhotos, setLocalPhotos] = useState<LocalPhoto[]>([]);

  useEffect(() => {
    return () => {
      localPhotos.forEach((photo) => URL.revokeObjectURL(photo.previewUrl));
    };
  }, [localPhotos]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) {
      return;
    }

    const selectedFiles = Array.from(files);
    const photos = selectedFiles.map((file) => ({
      fileName: file.name,
      previewUrl: URL.createObjectURL(file)
    }));
    setLocalPhotos(photos);
    processQuestionPhotos(photos);

    try {
      const result = await submitPhotos(selectedFiles);
      setPhotoOcrResult(result);
    } catch (error) {
      setPhotoOcrResult({
        event_name: "",
        trayek_name: "",
        location: "",
        normalized_text: "",
        photo_count: selectedFiles.length,
        status: "failed",
        warnings: [error instanceof Error ? error.message : "OCR upload failed"]
      });
    }
  }

  return (
    <div className="panel-section">
      <h2 className="panel-heading">Foto Soal</h2>

      <div className="photo-actions">
        <button className="icon-button primary" type="button" onClick={() => cameraRef.current?.click()}>
          <Camera size={16} /> Foto
        </button>
        <button className="icon-button" type="button" onClick={() => uploadRef.current?.click()}>
          <FileImage size={16} /> Upload
        </button>
      </div>

      <input
        ref={cameraRef}
        className="visually-hidden"
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <input
        ref={uploadRef}
        className="visually-hidden"
        type="file"
        accept="image/*"
        multiple
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div className="photo-strip">
        {(localPhotos.length > 0 ? localPhotos : photoOcr.photos).map((photo) => (
          <div className="photo-thumb" key={photo.fileName}>
            {photo.previewUrl ? <img alt={photo.fileName} src={photo.previewUrl} /> : <ScanText size={20} />}
            <span>{photo.fileName}</span>
          </div>
        ))}
      </div>

      <div className="ocr-status">
        <span className={`status-pill timing-${photoOcr.status === "failed" ? "error" : "warning"}`}>
          {photoOcr.status}
        </span>
        <p>{photoOcr.lastMessage}</p>
      </div>

      <div className="detected-fields">
        <span>Lomba: {photoOcr.detectedFields.eventName ?? "-"}</span>
        <span>Trayek: {photoOcr.detectedFields.trayekName ?? "-"}</span>
        <span>Lokasi: {photoOcr.detectedFields.location ?? "-"}</span>
        <span>Jarak: {photoOcr.detectedFields.totalDistanceKm?.toFixed(2) ?? "-"} km</span>
        <span>Waktu: {photoOcr.detectedFields.totalTimeMinutes ?? "-"} menit</span>
      </div>
    </div>
  );
}
