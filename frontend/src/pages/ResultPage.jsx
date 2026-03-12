import React, { useEffect, useState } from 'react';
import { CheckCircle, ArrowRight, Loader2, XCircle } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

export function ResultPage() {
    const { id } = useParams();
    const [job, setJob] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Poll for status
        const poll = setInterval(() => {
            fetch(`http://localhost:8000/jobs/${id}`)
                .then(res => res.json())
                .then(data => {
                    setJob(data);
                    if (data.status === 'completed' || data.status === 'failed') {
                        setLoading(false);
                        clearInterval(poll);
                    }
                })
                .catch(err => console.error(err));
        }, 2000);

        return () => clearInterval(poll);
    }, [id]);

    // Progress simulation
    const [progressStep, setProgressStep] = useState(0);
    const [seconds, setSeconds] = useState(0);

    const STEPS = [
        "Analyzing image quality...",
        "Constructing 3D geometry...",
        "Optimizing model for AR...",
        "Polishing textures...",
        "Finalizing output files..."
    ];

    useEffect(() => {
        if (!loading) return;

        // Timer
        const timer = setInterval(() => {
            setSeconds(s => s + 1);
        }, 1000);

        // Step cycler (every 8 seconds move to next step, cap at last one)
        const stepper = setInterval(() => {
            setProgressStep(prev => Math.min(prev + 1, STEPS.length - 1));
        }, 8000);

        return () => {
            clearInterval(timer);
            clearInterval(stepper);
        };
    }, [loading]);

    if (!job || loading) {
        return (
            <div className="max-w-3xl mx-auto text-center pt-32">
                <div className="relative w-16 h-16 mx-auto mb-8">
                    <Loader2 className="w-full h-full animate-spin text-brown-500" />
                </div>

                <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                    {STEPS[progressStep]}
                </h2>

                <p className="text-gray-500 mb-8">
                    Time elapsed: {Math.floor(seconds / 60)}:{(seconds % 60).toString().padStart(2, '0')}
                </p>

                <div className="max-w-xs mx-auto bg-beige-200 rounded-full h-1.5 overflow-hidden">
                    <div
                        className="h-full bg-brown-500 transition-all duration-1000 ease-linear"
                        style={{ width: `${Math.min((seconds / 40) * 100, 95)}%` }}
                    />
                </div>
                <p className="text-xs text-gray-400 mt-3">Estimated time: ~1 minute</p>
            </div>
        );
    }

    const isSuccess = job.status === 'completed';

    return (
        <div className="max-w-3xl mx-auto text-center pt-12">
            {/* Status Icon */}
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 ${isSuccess ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                }`}>
                {isSuccess ? <CheckCircle className="w-10 h-10" /> : <XCircle className="w-10 h-10" />}
            </div>

            <h1 className="text-3xl font-semibold text-gray-900 mb-2">
                {isSuccess ? "Accepted" : "Failed"}
            </h1>
            <p className="text-gray-600 mb-2">
                {isSuccess ? "Meets the current ruleset" : "Did not meet constraints"}
            </p>
            <p className="text-lg font-medium text-gray-900 mb-12">Job ID: {id}</p>

            {/* Info Card */}
            {isSuccess && (
                <div className="bg-beige-50 rounded-2xl p-8 text-left max-w-xl mx-auto mb-10 border border-beige-200">
                    <h3 className="font-semibold text-gray-900 mb-4">Job Summary</h3>
                    <ul className="space-y-3">
                        <li className="flex items-start gap-3 text-gray-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                            <span><strong>Geometry:</strong> Optimized to &lt;100k triangles (Mobile Ready)</span>
                        </li>
                        <li className="flex items-start gap-3 text-gray-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                            <span><strong>Textures:</strong> Resized to 2K resolution (PBR)</span>
                        </li>
                        <li className="flex items-start gap-3 text-gray-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                            <span><strong>Safety:</strong> Passed intersection & manifold checks</span>
                        </li>
                        <li className="flex items-start gap-3 text-gray-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                            <span><strong>Formats:</strong> GLB (Android) + USDZ (iOS) generated</span>
                        </li>
                    </ul>
                </div>
            )}

            {/* Actions */}
            <div className="space-y-4">
                {isSuccess && job.result && (
                    <a
                        href={`http://localhost:8000${job.result}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-8 py-3 bg-brown-500 text-white rounded-xl font-medium hover:bg-brown-600 transition-colors shadow-sm"
                    >
                        Download GLB
                        <ArrowRight className="w-4 h-4" />
                    </a>
                )}

                <div>
                    <Link to="/samples" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
                        View sample jobs →
                    </Link>
                </div>
            </div>
        </div>
    );
}
