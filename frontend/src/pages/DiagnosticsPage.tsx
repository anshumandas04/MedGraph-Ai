import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Button } from '../components/ui/Button';

interface DiagnosticLog {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  request_id?: string;
  method?: string;
  path?: string;
  status_code?: number;
  duration_ms?: number;
  exception_type?: string;
  source_characters?: number;
  candidate_count?: number;
  event_count?: number;
  event_types?: string;
  document_type?: string;
  ocr_provider?: string;
  ai_provider?: string;
  status?: string;
  page_count?: number;
  pages_with_text?: number;
  http_status?: number;
}

interface LogsResponse {
  storage: string;
  retained_limit: number;
  returned: number;
  note: string;
  logs: DiagnosticLog[];
}

export const DiagnosticsPage: React.FC = () => {
  const [level, setLevel] = useState('ALL');
  const { data, error, isLoading, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['admin-logs', level],
    queryFn: async () => (await api.get<LogsResponse>('/admin/logs', { params: { limit: 200, level } })).data,
    refetchInterval: 10_000,
  });

  const downloadLogs = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data.logs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'medgraph-diagnostics-' + new Date().toISOString().replace(/:/g, '-') + '.json';
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="mx-auto max-w-6xl space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">System diagnostics</h2>
          <p className="mt-1 text-sm text-slate-600">Recent backend requests and application events. Patient request and response bodies are not shown.</p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="log-level" className="text-sm text-slate-600">Level</label>
          <select id="log-level" value={level} onChange={(event) => setLevel(event.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">
            {['ALL', 'ERROR', 'CRITICAL', 'WARNING', 'INFO', 'DEBUG'].map((item) => <option key={item}>{item}</option>)}
          </select>
          <Button variant="outline" size="sm" onClick={() => { void refetch(); }}>Refresh</Button>
          <Button variant="outline" size="sm" onClick={downloadLogs} disabled={!data?.logs.length}>Download JSON</Button>
        </div>
      </header>

      <p className="text-xs text-slate-500">
        {data ? data.returned + ' entries · latest ' + new Date(dataUpdatedAt).toLocaleTimeString() + ' · ' + data.storage + ' buffer (last ' + data.retained_limit + ' entries; clears on backend restart)' : 'Loading log information…'}
      </p>

      {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">Could not load backend logs. Confirm you are signed in as an administrator, then refresh.</div>}
      {isLoading ? <p className="text-sm text-slate-500">Loading diagnostics…</p> : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr><th className="px-4 py-3">Time</th><th className="px-4 py-3">Level</th><th className="px-4 py-3">Request / event</th><th className="px-4 py-3">Result</th><th className="px-4 py-3">Request ID</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data?.logs.map((entry, index) => (
                <tr key={entry.timestamp + '-' + (entry.request_id ?? index)} className="align-top">
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">{new Date(entry.timestamp).toLocaleString()}</td>
                  <td className={'px-4 py-3 font-semibold ' + (entry.level === 'ERROR' || entry.level === 'CRITICAL' ? 'text-red-700' : entry.level === 'WARNING' ? 'text-amber-700' : 'text-slate-600')}>{entry.level}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">{entry.method && entry.path ? entry.method + ' ' + entry.path : entry.message}</div>
                    <div className="mt-1 text-xs text-slate-500">{entry.logger}{entry.exception_type ? ' · ' + entry.exception_type : ''}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {[
                        entry.status,
                        entry.document_type ? 'type=' + entry.document_type : '',
                        entry.ocr_provider ? 'OCR=' + entry.ocr_provider : '',
                        entry.ai_provider ? 'AI=' + entry.ai_provider : '',
                        entry.page_count !== undefined ? 'pages=' + entry.page_count : '',
                        entry.pages_with_text !== undefined ? 'pages with text=' + entry.pages_with_text : '',
                        entry.source_characters !== undefined ? 'characters=' + entry.source_characters : '',
                        entry.candidate_count !== undefined ? 'candidates=' + entry.candidate_count : '',
                        entry.event_count !== undefined ? 'events=' + entry.event_count : '',
                        entry.event_types ? 'event types=' + entry.event_types : '',
                        entry.http_status !== undefined ? 'provider HTTP=' + entry.http_status : '',
                      ].filter(Boolean).join(' · ')}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">{entry.status_code ?? '—'}{entry.duration_ms !== undefined ? ' · ' + entry.duration_ms + ' ms' : ''}</td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">{entry.request_id ?? '—'}</td>
                </tr>
              ))}
              {!data?.logs.length && <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-500">No log entries match this filter yet. Try Refresh after reproducing the issue.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-slate-500">For container startup errors that occur before this page is available, run <code>docker compose logs --since=30m backend</code> in PowerShell from the project folder.</p>
    </section>
  );
};
