import { useState } from 'react';
import api from '../services/api';

export default function Tools() {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [tool, setTool] = useState('payment');
  const [action, setAction] = useState('refund');
  const [amount, setAmount] = useState('100');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSimulate = async (e) => {
    e.preventDefault();
    setResult(null);
    setError(null);
    try {
      const payload = {
        identity: clientId,
        tool,
        action,
        resource: 'simulation',
        parameters: { amount: parseFloat(amount) }
      };
      
      const res = await api.post('/gateway/execute', payload, {
        headers: {
          'x-client-id': clientId,
          'x-client-secret': clientSecret
        }
      });
      setResult(res.data);
    } catch (err) {
      if (err.response) {
        setError(err.response.data);
      } else {
        setError(err.message);
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Gateway Simulator</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium mb-4">Simulate Request</h2>
          <form onSubmit={handleSimulate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Client ID (Identity Name)</label>
              <input type="text" value={clientId} onChange={(e) => setClientId(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Client Secret</label>
              <input type="password" value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Tool</label>
              <select value={tool} onChange={(e) => setTool(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2">
                <option value="payment">Payment</option>
                <option value="database">Database</option>
                <option value="customer">Customer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Action</label>
              <input type="text" value={action} onChange={(e) => setAction(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Amount (if applicable)</label>
              <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" />
            </div>
            
            <button type="submit" className="w-full bg-blue-600 text-white px-4 py-2 rounded">Execute Request</button>
          </form>
        </div>
        
        <div className="bg-gray-900 text-green-400 p-6 rounded-lg shadow font-mono text-sm overflow-auto">
          <h2 className="text-white text-lg font-medium mb-4 font-sans">Execution Result</h2>
          {result && (
            <div>
              <span className="text-gray-400">Response:</span>
              <pre className="mt-2">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
          {error && (
            <div className="text-red-400">
              <span className="text-gray-400">Error:</span>
              <pre className="mt-2">{JSON.stringify(error, null, 2)}</pre>
            </div>
          )}
          {!result && !error && <div className="text-gray-500">Awaiting request...</div>}
        </div>
      </div>
    </div>
  );
}
