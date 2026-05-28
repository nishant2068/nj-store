import React, { useState, useRef } from 'react';
import { Camera, Upload, Link as LinkIcon, X } from 'lucide-react';

export default function ProductImageUpload({ onImageUrl, initialUrl = '' }) {
  const [imageUrl, setImageUrl] = useState(initialUrl);
  const [preview, setPreview] = useState(initialUrl);
  const [loading, setLoading] = useState(false);
  const [uploadMode, setUploadMode] = useState(null);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);

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
  // URL Import
  const handleUrlImport = async () => {
    const url = prompt('Enter image URL:');
    if (!url) return;

    setLoading(true);
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64 = e.target?.result;
        await uploadBase64(base64);
      };
      reader.readAsDataURL(blob);
    } catch (error) {
      alert('Failed to fetch image: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Camera Capture
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      alert('Camera access denied: ' + error.message);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (context) {
        context.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
        const base64 = canvasRef.current.toDataURL('image/jpeg');
        uploadBase64(base64);
        stopCamera();
      }
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      setCameraActive(false);
    }
  };

  // Upload Base64
  const uploadBase64 = async (base64) => {
    setLoading(true);
    try {
      const response = await fetch('/api/upload-base64', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: base64 }),
      });
      const data = await response.json();
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

  return (
    <div className="space-y-4">
      {/* Preview */}
      {preview && (
        <div className="relative w-full h-48 bg-gray-100 rounded-lg overflow-hidden">
          <img src={preview} alt="Preview" className="w-full h-full object-cover" />
          <button
            onClick={() => {
              setImageUrl('');
              setPreview('');
              onImageUrl('');
            }}
            className="absolute top-2 right-2 bg-red-500 text-white p-1 rounded hover:bg-red-600"
          >
            <X size={20} />
          </button>
        </div>
      )}

      {/* Upload Mode Selection */}
      {!uploadMode ? (
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => setUploadMode('file')}
            className="flex flex-col items-center gap-2 p-3 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50"
          >
            <Upload size={24} className="text-blue-500" />
            <span className="text-sm font-medium">Upload File</span>
          </button>

          <button
            onClick={() => setUploadMode('url')}
            className="flex flex-col items-center gap-2 p-3 border-2 border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50"
          >
            <LinkIcon size={24} className="text-green-500" />
            <span className="text-sm font-medium">From URL</span>
          </button>

          <button
            onClick={() => {
              setUploadMode('camera');
              startCamera();
            }}
            className="flex flex-col items-center gap-2 p-3 border-2 border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50"
          >
            <Camera size={24} className="text-purple-500" />
            <span className="text-sm font-medium">Camera</span>
          </button>
        </div>
      ) : null}

      {/* File Upload */}
      {uploadMode === 'file' && (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Uploading...' : 'Select Image'}
          </button>
          <button
            onClick={() => setUploadMode(null)}
            className="w-full mt-2 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      )}

      {/* URL Import */}
      {uploadMode === 'url' && (
        <div>
          <button
            onClick={handleUrlImport}
            disabled={loading}
            className="w-full bg-green-500 text-white py-2 rounded-lg hover:bg-green-600 disabled:bg-gray-400"
          >
            {loading ? 'Loading...' : 'Enter URL'}
          </button>
          <button
            onClick={() => setUploadMode(null)}
            className="w-full mt-2 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Camera Capture */}
      {uploadMode === 'camera' && (
        <div>
          {cameraActive ? (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-48 bg-black rounded-lg"
              />
              <canvas ref={canvasRef} className="hidden" width={640} height={480} />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={capturePhoto}
                  disabled={loading}
                  className="flex-1 bg-purple-500 text-white py-2 rounded-lg hover:bg-purple-600 disabled:bg-gray-400"
                >
                  {loading ? 'Uploading...' : 'Capture Photo'}
                </button>
                <button
                  onClick={stopCamera}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </>
          ) : (
            <>
              <button
                onClick={startCamera}
                className="w-full bg-purple-500 text-white py-2 rounded-lg hover:bg-purple-600"
              >
                Start Camera
              </button>
              <button
                onClick={() => setUploadMode(null)}
                className="w-full mt-2 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
