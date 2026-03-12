import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Box } from 'lucide-react';

export function Layout({ children }) {
    const location = useLocation();

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="bg-beige-100 border-b border-beige-200 px-8 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Box className="w-6 h-6 text-gray-800" />
                    <span className="text-lg font-semibold tracking-wide text-gray-900">AUGMINTED</span>
                    <span className="ml-2 px-2 py-0.5 bg-beige-200 text-xs text-gray-600 rounded-md border border-beige-300">
                        Portal
                    </span>
                </div>

                <nav className="flex items-center gap-6">
                    <Link
                        to="/"
                        className={`text-sm font-medium transition-colors ${location.pathname === '/' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-900'
                            }`}
                    >
                        Upload
                    </Link>
                    <Link
                        to="/samples"
                        className={`text-sm font-medium transition-colors ${location.pathname === '/samples' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-900'
                            }`}
                    >
                        Samples
                    </Link>
                </nav>
            </header>

            {/* Main Content */}
            <main className="flex-1 w-full max-w-7xl mx-auto px-8 py-12">
                {children}
            </main>

            {/* Footer */}
            <footer className="px-8 py-6 text-xs text-gray-400 flex justify-between max-w-7xl mx-auto w-full">
                <span>Augminted Portal — Demo</span>
                <span>Back to main site</span>
            </footer>
        </div>
    );
}
