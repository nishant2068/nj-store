import React, { useState, useRef } from 'react';
import { Camera, Upload, Link as LinkIcon, X } from 'lucide-react';

export default function ProductImageUpload({
  onImageUrl,
  initialUrl = '',
}) {
  const [imageUrl, setImageUrl] = useState(initialUrl);
  const [preview, setPreview] = useState(initialUrl);
  const [loading, setLoading] = useState(false);
  const [uploadMode, setUploadMode] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // =====================================================
  // FILE UPLOAD
  // =====================================================

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];

    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setImageUrl(data.url);
      setPreview(data.url);
      onImageUrl(data.url);

      setUploadMode(null);
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // URL IMPORT
  // =====================================================

  const handleUrlImport = async () => {
    const url = prompt('Enter image URL:');

    if (!url) return;

    setLoading(true);

    try {
      const response = await fetch('/api/upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setImageUrl(data.url);
      setPreview(data.url);
      onImageUrl(data.url);

      setUploadMode(null);
    } catch (error) {
      alert('Failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // CAMERA
  // =====================================================

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      setCameraActive(true);
    } catch (error) {
      alert('Camera access denied');
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject
        .getTracks()
        .forEach((track) => track.stop());
    }

    setCameraActive(false);
  };

  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;

    canvas.width = 640;
    canvas.height = 480;

    const ctx = canvas.getContext('2d');

    ctx.drawImage(videoRef.current, 0, 0, 640, 480);

    const base64 = canvas.toDataURL('image/jpeg');

    await uploadBase64(base64);

    stopCamera();
  };

  // =====================================================
  // BASE64 UPLOAD
  // =====================================================

  const uploadBase64 = async (base64) => {
    setLoading(true);

    try {
      const response = await fetch('/api/upload-base64', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: base64,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setImageUrl(data.url);
      setPreview(data.url);
      onImageUrl(data.url);

      setUploadMode(null);
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // UI
  // =====================================================

  return (
    <div className="space-y-4">

      {/* PREVIEW */}
      {preview && (
        <div className="relative w-full h-48 bg-gray-100 rounded-lg overflow-hidden">
          <img
            src={preview}
            alt="Preview"
            className="w-full h-full object-cover"
          />

          <button
            onClick={() => {
              setImageUrl('');
              setPreview('');
              onImageUrl('');
            }}
            className="absolute top-2 right-2 bg-red-500 text-white p-1 rounded hover:bg-red-600"
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* SELECT MODE */}
      {!uploadMode && (
        <div className="grid grid-cols-3 gap-3">

          <button
            onClick={() => setUploadMode('file')}
            className="flex flex-col items-center gap-2 p-3 border rounded-lg hover:bg-gray-50"
          >
            <Upload size={24} />
            <span className="text-sm">Upload</span>
          </button>

          <button
            onClick={() => setUploadMode('url')}
            className="flex flex-col items-center gap-2 p-3 border rounded-lg hover:bg-gray-50"
          >
            <LinkIcon size={24} />
            <span className="text-sm">URL</span>
          </button>

          <button
            onClick={() => {
              setUploadMode('camera');
              startCamera();
            }}
            className="flex flex-col items-center gap-2 p-3 border rounded-lg hover:bg-gray-50"
          >
            <Camera size={24} />
            <span className="text-sm">Camera</span>
          </button>

        </div>
      )}

      {/* FILE */}
      {uploadMode === 'file' && (
        <div>

          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 rounded-lg"
          >
            {loading ? 'Uploading...' : 'Select Image'}
          </button>

          <button
            onClick={() => setUploadMode(null)}
            className="w-full mt-2 bg-gray-300 py-2 rounded-lg"
          >
            Cancel
          </button>

        </div>
      )}

      {/* URL */}
      {uploadMode === 'url' && (
        <div>

          <button
            onClick={handleUrlImport}
            disabled={loading}
            className="w-full bg-green-500 text-white py-2 rounded-lg"
          >
            {loading ? 'Loading...' : 'Enter URL'}
          </button>

          <button
            onClick={() => setUploadMode(null)}
            className="w-full mt-2 bg-gray-300 py-2 rounded-lg"
          >
            Cancel
          </button>

        </div>
      )}

      {/* CAMERA */}
      {uploadMode === 'camera' && (
        <div>

          {cameraActive && (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-48 bg-black rounded-lg"
              />

              <canvas
                ref={canvasRef}
                className="hidden"
              />

              <div className="flex gap-2 mt-2">

                <button
                  onClick={capturePhoto}
                  disabled={loading}
                  className="flex-1 bg-purple-500 text-white py-2 rounded-lg"
                >
                  {loading ? 'Uploading...' : 'Capture'}
                </button>

                <button
                  onClick={() => {
                    stopCamera();
                    setUploadMode(null);
                  }}
                  className="flex-1 bg-gray-300 py-2 rounded-lg"
                >
                  Cancel
                </button>

              </div>
            </>
          )}

        </div>
      )}

    </div>
  );
}
