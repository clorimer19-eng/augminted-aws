import React, { useState } from 'react';
import { Upload, FileText, ChevronDown, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function UploadPage() {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const navigate = useNavigate();

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await uploadFiles(files);
        }
    };

    const handleBrowse = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = 'image/*';
        input.onchange = (e) => {
            if (e.target.files.length > 0) {
                uploadFiles(e.target.files);
            }
        };
        input.click();
    };

    const uploadFiles = async (files) => {
        setIsUploading(true);
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        // Collect specs
        const material = document.querySelector('select[name="material"]')?.value || "";
        const finish = document.querySelector('select[name="finish"]')?.value || "";
        const color = document.querySelector('input[name="color_desc"]')?.value || "";

        formData.append('specs', JSON.stringify({ material, finish, color }));

        try {
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                // Navigate to result page (polling will happen there)
                navigate(`/job/${data.job_id}`);
            } else {
                console.error('Upload failed');
                alert('Upload failed. Please try again.');
            }
        } catch (error) {
            console.error('Error uploading:', error);
            alert('Error uploading. Is the backend running?');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto">
            <div className="text-center mb-10">
                <h1 className="text-3xl font-semibold text-gray-900 mb-3">Upload product files</h1>
                <p className="text-gray-600">Add your product images and optional 3D files for checking.</p>
            </div>

            <div className="space-y-8">
                {/* Demo Selector */}
                <div className="flex items-center gap-4 justify-center">
                    <span className="text-gray-600">For demo:</span>
                    <button className="flex items-center gap-2 px-4 py-2 bg-beige-200 rounded-md text-gray-800 hover:bg-beige-300 transition-colors">
                        <span>Choose a sample job</span>
                        <ChevronDown className="w-4 h-4" />
                    </button>
                </div>

                {/* Main Upload Area */}
                <div className="space-y-2">
                    <h2 className="text-sm font-medium text-gray-700">Product images</h2>
                    <div
                        className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-colors ${isDragging ? 'border-brown-500 bg-beige-50' : 'border-gray-300 bg-white'
                            }`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <div className="w-12 h-12 mb-4 text-gray-400">
                            {isUploading ? <Loader2 className="w-full h-full animate-spin" /> : <Upload className="w-full h-full" />}
                        </div>
                        <p className="text-lg text-gray-700 mb-2">
                            {isUploading ? "Uploading..." : "Drag and drop JPG or PNG files here"}
                        </p>
                        <p className="text-sm text-gray-500 mb-6">or</p>
                        <button
                            onClick={handleBrowse}
                            disabled={isUploading}
                            className="px-6 py-2 bg-beige-200 text-gray-800 rounded-md font-medium hover:bg-beige-300 transition-colors disabled:opacity-50"
                        >
                            Browse files
                        </button>
                    </div>
                </div>

                {/* Furniture Specs Questionnaire */}
                <div className="space-y-4">
                    <h2 className="text-sm font-medium text-gray-700">Material Details</h2>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs text-gray-500">Primary Material</label>
                            <select
                                name="material"
                                className="w-full p-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-brown-500/20 appearance-none"
                            >
                                <option value="">Select...</option>
                                <option value="wood">Wood</option>
                                <option value="metal">Metal</option>
                                <option value="plastic">Plastic</option>
                                <option value="fabric">Fabric</option>
                                <option value="leather">Leather</option>
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs text-gray-500">Finish</label>
                            <select
                                name="finish"
                                className="w-full p-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-brown-500/20 appearance-none"
                            >
                                <option value="">Select...</option>
                                <option value="matte">Matte</option>
                                <option value="satin">Satin</option>
                                <option value="gloss">Gloss</option>
                                <option value="textured">Textured</option>
                            </select>
                        </div>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs text-gray-500">Color / Texture Description</label>
                        <input
                            type="text"
                            name="color_desc"
                            placeholder="e.g. Dark Walnut, Brushed Gold, Navy Blue Velvet"
                            className="w-full p-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-brown-500/20"
                        />
                    </div>
                </div>

                {/* Optional 3D Files */}
                <div className="space-y-2">
                    <h2 className="text-sm font-medium text-gray-700">Output files (optional)</h2>
                    <div
                        className="border-2 border-dashed border-gray-300 rounded-xl p-8 flex flex-col items-center justify-center bg-white"
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <FileText className="w-8 h-8 text-gray-400 mb-3" />
                        <p className="text-sm text-gray-600 mb-2">Drop GLB or USDZ files here</p>
                        <button
                            onClick={handleBrowse}
                            className="text-brown-600 font-medium hover:underline text-sm"
                        >
                            Browse
                        </button>
                    </div>
                </div>

                {/* CTA */}
                <button className="w-full py-4 bg-brown-500 text-white rounded-xl font-medium text-lg hover:bg-brown-600 transition-colors shadow-sm">
                    Check product fit
                </button>
            </div>
        </div>
    );
}
