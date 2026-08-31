import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    identities: 0,
    activePolicies: 0,
    recentEvents: 0,
  });
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [identitiesRes, policiesRes, logsRes] = await Promise.all([
          api.get('/workloads'),
          api.get('/policies'),
          api.get('/audit/logs?limit=100')
        ]);
        
        setStats({
          identities: identitiesRes.data.length,
          activePolicies: policiesRes.data.filter(p => p.is_enabled).length,
          recentEvents: logsRes.data.length,
        });
        
        setLogs(logsRes.data);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      }
    };
    fetchData();
  }, []);

  const chartData = [
    { name: 'ALLOW', count: logs.filter(l => l.decision === 'ALLOW').length },
    { name: 'DENY', count: logs.filter(l => l.decision === 'DENY').length },
    { name: 'APPROVAL', count: logs.filter(l => l.decision === 'REQUIRE_APPROVAL').length },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Security Overview</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3 text-gray-500 mb-2">
            <Shield className="h-5 w-5" />
            <span className="font-medium">Active Workloads</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.identities}</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3 text-gray-500 mb-2">
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Active Policies</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.activePolicies}</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3 text-gray-500 mb-2">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-medium">Recent Events</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.recentEvents}</div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 h-96">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Decisions Overview</h2>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Dashboard;
