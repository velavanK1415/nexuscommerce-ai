import React, { useState, useMemo, useRef, useCallback } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  DollarSign, 
  Download, 
  Filter, 
  Search, 
  ArrowUpDown,
  Sparkles,
  PieChart,
  Layers,
  ChevronRight,
  CheckCircle2,
  Table
} from './icons';

// AG Grid Community & React Imports
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function AGStudioSpendGrid({ summary, gridData, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [viewMode, setViewMode] = useState('ag-grid'); // 'ag-grid' | 'table'
  const gridRef = useRef(null);

  const rows = gridData?.rows || [];

  // Filter & Search
  const filteredRows = useMemo(() => {
    return rows.filter((r) => {
      const matchesSearch =
        !searchTerm ||
        r.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.vendor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.order_id.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCat = selectedCategory === 'ALL' || r.category === selectedCategory;
      return matchesSearch && matchesCat;
    });
  }, [rows, searchTerm, selectedCategory]);

  const categories = useMemo(() => {
    const cats = new Set(rows.map((r) => r.category).filter(Boolean));
    return ['ALL', ...Array.from(cats)];
  }, [rows]);

  // AG Grid Column Definitions
  const columnDefs = useMemo(() => [
    {
      field: 'order_id',
      headerName: 'Order Ref',
      width: 140,
      pinned: 'left',
      cellClass: 'font-mono font-bold text-cyan-400',
      checkboxSelection: true,
      filter: true,
      sortable: true,
    },
    {
      field: 'item_name',
      headerName: 'Procured Asset',
      width: 250,
      filter: true,
      sortable: true,
      cellRenderer: (params) => (
        <div className="py-1">
          <div className="font-semibold text-white leading-tight">{params.value}</div>
          <div className="text-[10px] text-slate-400">{params.data?.category}</div>
        </div>
      ),
    },
    {
      field: 'vendor_name',
      headerName: 'Supplier',
      width: 210,
      filter: true,
      sortable: true,
      cellClass: 'text-slate-200',
    },
    {
      field: 'quantity',
      headerName: 'Qty',
      width: 90,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      cellClass: 'font-mono text-slate-200 text-right',
    },
    {
      field: 'catalog_ask_price',
      headerName: 'Catalog Ask ($)',
      width: 140,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      valueFormatter: (p) => p.value ? `$${p.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '-',
      cellClass: 'font-mono text-slate-400 text-right',
    },
    {
      field: 'settled_unit_price',
      headerName: 'Settled Unit ($)',
      width: 140,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      valueFormatter: (p) => p.value ? `$${p.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '-',
      cellClass: 'font-mono text-emerald-400 font-bold text-right',
    },
    {
      field: 'total_spend',
      headerName: 'Total Settled ($)',
      width: 150,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      valueFormatter: (p) => p.value ? `$${p.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '-',
      cellClass: 'font-mono text-white font-bold text-right',
    },
    {
      field: 'savings_achieved',
      headerName: 'Agent Savings ($)',
      width: 150,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      valueFormatter: (p) => p.value ? `+$${p.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '$0.00',
      cellClass: 'font-mono text-green-400 font-bold text-right',
    },
    {
      field: 'savings_pct',
      headerName: 'Alpha %',
      width: 110,
      filter: 'agNumberColumnFilter',
      sortable: true,
      type: 'numericColumn',
      valueFormatter: (p) => `${p.value}%`,
      cellClass: 'font-mono text-cyan-300 font-bold text-right',
    },
    {
      field: 'status',
      headerName: 'Settlement Status',
      width: 150,
      filter: true,
      sortable: true,
      cellRenderer: (params) => {
        const status = params.value;
        const color =
          status === 'COMPLETED'
            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
            : status === 'IN_TRANSIT'
            ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            : 'bg-blue-500/20 text-blue-300 border-blue-500/30';
        return (
          <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border ${color}`}>
            {status}
          </span>
        );
      },
    },
    {
      field: 'bundle_hash',
      headerName: 'Audit Root SHA-256',
      width: 180,
      cellClass: 'font-mono text-[11px] text-amber-300/80',
    },
  ], []);

  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: false,
  }), []);

  const exportCSV = useCallback(() => {
    if (gridRef.current?.api) {
      gridRef.current.api.exportDataAsCsv({
        fileName: `NexusCommerce_AGStudio_Spend_${new Date().toISOString().slice(0, 10)}.csv`,
      });
      return;
    }

    // Manual fallback export
    const headers = ['Order Ref', 'Mandate ID', 'Asset', 'Category', 'Supplier', 'Qty', 'Catalog Ask ($)', 'Settled Unit ($)', 'Total Settled ($)', 'Savings ($)', 'Alpha %', 'Status', 'PayPal Auth'];
    const csvRows = filteredRows.map(r => [
      r.order_id,
      r.mandate_id,
      `"${r.item_name}"`,
      `"${r.category}"`,
      `"${r.vendor_name}"`,
      r.quantity,
      r.catalog_ask_price,
      r.settled_unit_price,
      r.total_spend,
      r.savings_achieved,
      r.savings_pct,
      r.status,
      r.paypal_auth_id,
    ]);

    const content = [headers.join(','), ...csvRows.map(row => row.join(','))].join('\n');
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NexusCommerce_AGStudio_Spend_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  }, [filteredRows]);

  return (
    <div className="space-y-6">
      
      {/* Sponsor Prize Banner */}
      <div className="bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-blue-900/40 border border-indigo-500/30 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-400 to-amber-600 flex items-center justify-center text-slate-950 font-black text-sm shadow-md shadow-amber-500/30">
              AG
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white">AG Studio & AG Grid Spend Intelligence</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Targeting $5,000 AG Studio Hackathon Prize
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Self-serve transactional intelligence, negotiation alpha metrics, and automated audit ledger powered by AG Grid
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="bg-slate-900/80 p-1 rounded-xl border border-slate-700 flex items-center space-x-1">
              <button
                onClick={() => setViewMode('ag-grid')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  viewMode === 'ag-grid'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>AG Grid Engine</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  viewMode === 'table'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Table className="w-3.5 h-3.5" />
                <span>Compact Table</span>
              </button>
            </div>

            <button
              onClick={exportCSV}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition-all shadow"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export AG Grid CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Alpha Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        
        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Spend Under Mgmt
          </span>
          <div className="text-xl font-extrabold text-white font-mono">
            ${(summary?.total_spend_under_management || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center space-x-1">
            <TrendingUp className="w-3 h-3" />
            <span>100% Auth Hold Protected</span>
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Realized Agent Savings
          </span>
          <div className="text-xl font-extrabold text-emerald-400 font-mono">
            ${(summary?.total_savings_generated || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Vs Catalog Ask Prices</div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Negotiation Alpha
          </span>
          <div className="text-xl font-extrabold text-cyan-400 font-mono">
            {summary?.average_procurement_alpha_pct || 0}%
          </div>
          <div className="text-[11px] text-cyan-300/80 mt-1">Autonomous Margin Lift</div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Dispute Protection
          </span>
          <div className="text-xl font-extrabold text-indigo-400 font-mono">
            100%
          </div>
          <div className="text-[11px] text-indigo-300 mt-1 flex items-center space-x-1">
            <ShieldCheck className="w-3 h-3" />
            <span>Cryptographic Proof</span>
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            HITL Holds Prevented
          </span>
          <div className="text-xl font-extrabold text-amber-400 font-mono">
            {summary?.hitl_policy_violations_prevented || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Zero Budget Breaches</div>
        </div>
      </div>

      {/* Search & Category Filter Controls */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by asset, supplier, or order ref..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-indigo-500"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c === 'ALL' ? 'All Categories' : c}
                </option>
              ))}
            </select>
          </div>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Showing {filteredRows.length} of {rows.length} transactions · Active Engine: {viewMode === 'ag-grid' ? 'AG Grid v36' : 'HTML Grid'}
        </span>
      </div>

      {/* Grid Content Display */}
      {viewMode === 'ag-grid' ? (
        <div className="bg-[#111827] border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-2">
          <div className="ag-theme-alpine-dark w-full" style={{ height: '480px', width: '100%' }}>
            <AgGridReact
              ref={gridRef}
              rowData={filteredRows}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              pagination={true}
              paginationPageSize={10}
              quickFilterText={searchTerm}
              rowSelection="multiple"
              animateRows={true}
            />
          </div>
        </div>
      ) : (
        <div className="bg-[#111827] border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Order Ref</th>
                  <th className="px-4 py-3">Procured Asset</th>
                  <th className="px-4 py-3">Supplier</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Settled Unit</th>
                  <th className="px-4 py-3 text-right">Total Spend</th>
                  <th className="px-4 py-3 text-right">Agent Savings</th>
                  <th className="px-4 py-3 text-right">Alpha %</th>
                  <th className="px-4 py-3 text-center">Settlement Status</th>
                  <th className="px-4 py-3 text-right">Audit SHA-256</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {filteredRows.length === 0 ? (
                  <tr>
                    <td colSpan="10" className="px-4 py-8 text-center text-slate-500 text-xs">
                      No transactions match current filters.
                    </td>
                  </tr>
                ) : (
                  filteredRows.map((row, idx) => (
                    <tr
                      key={row.order_id || idx}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono font-bold text-cyan-400">
                        {row.order_id}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-white">{row.item_name}</div>
                        <div className="text-[10px] text-slate-400">{row.category}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-200">{row.vendor_name}</td>
                      <td className="px-4 py-3 font-mono text-right text-slate-200">{row.quantity}</td>
                      <td className="px-4 py-3 font-mono text-right text-emerald-400">
                        ${row.settled_unit_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 font-mono text-right font-bold text-white">
                        ${row.total_spend.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 font-mono text-right text-green-400 font-bold">
                        +${row.savings_achieved.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 font-mono text-right text-cyan-300 font-bold">
                        {row.savings_pct}%
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            row.status === 'COMPLETED'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : row.status === 'IN_TRANSIT'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-right text-[10px] text-amber-300/80">
                        {row.bundle_hash}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
