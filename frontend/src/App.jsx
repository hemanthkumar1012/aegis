import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Identities from './pages/Identities';
import Policies from './pages/Policies';
import Audit from './pages/Audit';
import Approvals from './pages/Approvals';
import Tools from './pages/Tools';

function App() {
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="identities" element={<Identities />} />
          <Route path="policies" element={<Policies />} />
          <Route path="audit" element={<Audit />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="tools" element={<Tools />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
