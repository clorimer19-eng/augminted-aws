import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Play, ArrowLeft, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';

function StatusBadge({ status }) {
    const isAccepted = status === 'completed'; // Mapping 'completed' to Accepted for now
    const isProcessing = status === 'processing';

    if (isProcessing) {
        return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Processing
            </span>
        );
    }

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${isAccepted ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
            }`}>
            {isAccepted ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
            {isAccepted ? "Accepted" : status}
        </span>
    );
}

function JobCard({ job }) {
    const isAccepted = job.status === 'completed';

    return (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-sm text-gray-500">{job.category}</p>
                </div>
                <StatusBadge status={job.status} />
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-2 gap-4 mb-4">
                {/* Input */}
                <div className="space-y-2">
                    <span className="text-xs text-gray-500">Input</span>
                    <div className="aspect-square rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center">
                        {/* Placeholder for now */}
                        <span className="text-xs text-gray-400">Image</span>
                    </div>
                </div>

                {/* Output */}
                <div className="space-y-2">
                    <span className="text-xs text-gray-500">Output</span>
                    {isAccepted ? (
                        <div className="aspect-square rounded-lg bg-beige-200 flex items-center justify-center text-brown-600 text-sm font-medium">
                            3D Ready
                        </div>
                    ) : (
                        <div className="aspect-square rounded-lg bg-gray-100 flex items-center justify-center text-gray-400 text-sm">
                            Not processed
                        </div>
                    )}
                </div>
            </div>

            {/* Footer / Actions */}
            {isAccepted ? (
                <>
                    <div className="flex gap-2 mb-4">
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">Clean geometry</span>
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">Good coverage</span>
                    </div>
                    <Link
                        to={`/job/${job.id}`}
                        className="w-full flex items-center justify-center gap-2 py-2.5 bg-beige-50 border border-beige-200 rounded-lg text-gray-700 font-medium hover:bg-beige-100 transition-colors"
                    >
                        <Play className="w-4 h-4" />
                        Run this sample
                    </Link>
                </>
            ) : (
                <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500">Processing...</p>
                </div>
            )}
        </div>
    );
}

export function SamplesPage() {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/jobs')
            .then(res => res.json())
            .then(data => {
                setJobs(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch jobs", err);
                setLoading(false);
            });
    }, []);

    return (
        <div className="max-w-5xl mx-auto">
            <div className="mb-8">
                <Link to="/" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft className="w-4 h-4 mr-1" />
                    Back to upload
                </Link>
                <h1 className="text-3xl font-semibold text-gray-900 mb-2">Sample jobs</h1>
                <p className="text-gray-600">Examples of products processed through the rules-based system.</p>
            </div>

            {loading ? (
                <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {jobs.length === 0 ? (
                        <p className="text-gray-500">No jobs found.</p>
                    ) : (
                        jobs.map(job => (
                            <JobCard key={job.id} job={job} />
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
