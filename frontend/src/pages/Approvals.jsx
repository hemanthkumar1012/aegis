import { useState, useEffect } from 'react';
import api from '../services/api';

export default function Approvals() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchApprovals = async () => {
    try {
      const res = await api.get('/approvals');
      setApprovals(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleReview = async (requestId, action) => {
    try {
      await api.post(`/approvals/${requestId}/review`, { action });
      fetchApprovals();
    } catch (err) {
      alert(`Failed to ${action} request`);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Pending Approvals</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Request ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Identity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Operation</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {approvals.map((req) => (
              <tr key={req.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{req.request_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{req.identity_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {req.action} on {req.tool}
                  <div className="text-xs mt-1 bg-gray-100 p-1 rounded">
                    {JSON.stringify(req.parameters)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    req.status === 'APPROVED' || req.status === 'EXECUTED' ? 'bg-green-100 text-green-800' :
                    req.status === 'REJECTED' || req.status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {req.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  {req.status === 'PENDING' && (
                    <>
                      <button onClick={() => handleReview(req.request_id, 'APPROVE')} className="text-green-600 hover:text-green-900">Approve</button>
                      <button onClick={() => handleReview(req.request_id, 'REJECT')} className="text-red-600 hover:text-red-900">Reject</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {approvals.length === 0 && <div className="p-6 text-center text-gray-500">No approval requests.</div>}
      </div>
    </div>
  );
}
