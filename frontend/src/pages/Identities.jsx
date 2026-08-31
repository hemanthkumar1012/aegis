import { useState, useEffect } from 'react';
import api from '../services/api';
import { Key, Ban, CheckCircle, Plus } from 'lucide-react';

export default function Identities() {
  const [identities, setIdentities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newIdentityName, setNewIdentityName] = useState('');

  const fetchIdentities = async () => {
    try {
      const res = await api.get('/workloads');
      setIdentities(res.data);
    } catch (err) {
      setError('Failed to fetch identities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdentities();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.post('/workloads', { name: newIdentityName, owner: 'admin', environment: 'prod' });
      setNewIdentityName('');
      fetchIdentities();
    } catch (err) {
      alert('Failed to create identity');
    }
  };

  const handleSuspend = async (id) => {
    try {
      await api.put(`/workloads/${id}/suspend`);
      fetchIdentities();
    } catch (err) {
      alert('Failed to suspend');
    }
  };

  const handleReactivate = async (id) => {
    try {
      await api.put(`/workloads/${id}/reactivate`);
      fetchIdentities();
    } catch (err) {
      alert('Failed to reactivate');
    }
  };

  const handleGenerateCreds = async (id) => {
    try {
      const res = await api.post(`/workloads/${id}/credentials`);
      alert(`Client ID: ${res.data.client_id}\nClient Secret: ${res.data.client_secret}\n\nSAVE THIS SECRET, IT WILL NOT BE SHOWN AGAIN.`);
    } catch (err) {
      alert('Failed to generate credentials');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Workload Identities</h1>
        
        <form onSubmit={handleCreate} className="flex space-x-2">
          <input
            type="text"
            value={newIdentityName}
            onChange={(e) => setNewIdentityName(e.target.value)}
            placeholder="New Identity Name"
            className="px-3 py-2 border rounded"
            required
          />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded flex items-center">
            <Plus className="h-4 w-4 mr-2" /> Create
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {identities.map((identity) => (
              <tr key={identity.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{identity.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${identity.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {identity.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(identity.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                  <button onClick={() => handleGenerateCreds(identity.id)} className="text-blue-600 hover:text-blue-900" title="Generate Credentials">
                    <Key className="h-5 w-5 inline" />
                  </button>
                  {identity.status === 'ACTIVE' ? (
                    <button onClick={() => handleSuspend(identity.id)} className="text-red-600 hover:text-red-900" title="Suspend">
                      <Ban className="h-5 w-5 inline" />
                    </button>
                  ) : (
                    <button onClick={() => handleReactivate(identity.id)} className="text-green-600 hover:text-green-900" title="Reactivate">
                      <CheckCircle className="h-5 w-5 inline" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {identities.length === 0 && (
          <div className="p-6 text-center text-gray-500">No identities found.</div>
        )}
      </div>
    </div>
  );
}
