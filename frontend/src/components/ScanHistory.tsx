import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Job } from '../api';

interface Props {
  onViewJob: (jobId: string) => void;
}

export default function ScanHistory({ onViewJob }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.listJobs();
        setJobs(data.jobs);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const statusBadge = (status: string) => {
    switch (status) {
      case 'completed': return 'badge-success';
      case 'running': return 'badge-running';
      case 'failed': return 'badge-failed';
      default: return 'badge-non-sensitive';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-slide-up">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Scan History</h2>
        <p className="text-gray-400 mt-1">View past classification scans</p>
      </div>

      {jobs.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-semibold text-white mb-2">No scans yet</h3>
          <p className="text-gray-400 text-sm">
            Connect to a database and run your first scan to see results here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              onClick={() => job.status === 'completed' && onViewJob(job.id)}
              className={`glass-card-light p-5 transition-all duration-200 ${
                job.status === 'completed'
                  ? 'cursor-pointer hover:bg-gray-800/40 hover:border-gray-600/50'
                  : 'opacity-75'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gray-800/70 flex items-center justify-center">
                    <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">
                        {job.connection_info.database || 'Unknown DB'}
                      </span>
                      <span className={`badge ${statusBadge(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {job.connection_info.host}:{job.connection_info.port} •{' '}
                      {formatDate(job.created_at)}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-lg font-bold text-white">
                    {job.scanned_fields ?? 0}
                  </div>
                  <div className="text-xs text-gray-500">
                    fields scanned
                  </div>
                </div>
              </div>

              {job.error_message && (
                <div className="mt-3 text-xs text-red-400 bg-red-500/5 p-2 rounded-lg">
                  {job.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
