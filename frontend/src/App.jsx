import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './layouts/Layout';

import { UploadPage } from './pages/UploadPage';
import { SamplesPage } from './pages/SamplesPage';
import { ResultPage } from './pages/ResultPage';

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/" element={<UploadPage />} />
                    <Route path="/samples" element={<SamplesPage />} />
                    <Route path="/job/:id" element={<ResultPage />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}

export default App;
