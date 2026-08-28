import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import ChatTutor from '@/pages/ChatTutor';
import ArtDiagnosis from '@/pages/ArtDiagnosis';
import PaperInterpret from '@/pages/PaperInterpret';
import Archive from '@/pages/Archive';
import NotFound from '@/pages/NotFound';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<ChatTutor />} />
          <Route path="/chat" element={<ChatTutor />} />
          <Route path="/art-diagnosis" element={<ArtDiagnosis />} />
          <Route path="/paper-interpret" element={<PaperInterpret />} />
          <Route path="/archive" element={<Archive />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
