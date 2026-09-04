
import React from 'react';
import { useCms, Paper } from './CmsContext';
import { Settings, Save, RotateCcw, X, Plus, Trash2 } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { content, updateContent, resetToDefault, isAdmin, setAdmin } = useCms();

  if (!isAdmin) {
    return (
      <button 
        onClick={() => setAdmin(true)}
        className="fixed bottom-6 right-6 z-[100] p-4 bg-physics-cyan/20 border border-physics-cyan/40 text-physics-cyan rounded-full hover:bg-physics-cyan/40 transition-all shadow-lg backdrop-blur-md group"
      >
        <Settings className="group-hover:rotate-90 transition-transform duration-500" size={24} />
      </button>
    );
  }

  const handleHeroChange = (key: string, value: string) => {
    updateContent({ ...content, hero: { ...content.hero, [key]: value } });
  };

  const handlePaperChange = (id: string, title: string) => {
    const newPapers = content.papers.map(p => p.id === id ? { ...p, title } : p);
    updateContent({ ...content, papers: newPapers });
  };

  const removePaper = (id: string) => {
    updateContent({ ...content, papers: content.papers.filter(p => p.id !== id) });
  };

  const addPaper = () => {
    const newPaper: Paper = {
      id: Date.now().toString(),
      title: "New Research Paper",
      color: "text-physics-cyan",
      tag: "Addendum"
    };
    updateContent({ ...content, papers: [...content.papers, newPaper] });
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-96 bg-physics-card/95 backdrop-blur-xl border-l border-slate-800 z-[101] shadow-2xl flex flex-col animate-fade-in">
      <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-black/20">
        <h2 className="font-serif text-xl text-white flex items-center gap-2">
          <Settings size={20} className="text-physics-cyan" />
          Content Management
        </h2>
        <button onClick={() => setAdmin(false)} className="text-slate-400 hover:text-white transition-colors">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
        {/* Hero Editor */}
        <section className="space-y-4">
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-physics-muted border-b border-slate-800 pb-2">Hero Section</h3>
          <div className="space-y-3">
            <div>
              <label className="text-[10px] text-physics-cyan uppercase block mb-1">Title</label>
              <input 
                value={content.hero.title} 
                onChange={(e) => handleHeroChange('title', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-physics-cyan outline-none transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] text-physics-cyan uppercase block mb-1">Subtitle</label>
              <input 
                value={content.hero.subtitle} 
                onChange={(e) => handleHeroChange('subtitle', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-physics-cyan outline-none transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] text-physics-cyan uppercase block mb-1">Description</label>
              <textarea 
                value={content.hero.description} 
                onChange={(e) => handleHeroChange('description', e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-physics-cyan outline-none transition-colors resize-none"
              />
            </div>
          </div>
        </section>

        {/* Papers Editor */}
        <section className="space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-physics-muted">Papers (The Series)</h3>
            <button onClick={addPaper} className="text-physics-cyan hover:bg-physics-cyan/10 p-1 rounded transition-colors">
              <Plus size={16} />
            </button>
          </div>
          <div className="space-y-3">
            {content.papers.map((paper) => (
              <div key={paper.id} className="group flex gap-2 items-start">
                <div className="flex-1">
                  <input 
                    value={paper.title} 
                    onChange={(e) => handlePaperChange(paper.id, e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:border-physics-cyan outline-none transition-colors"
                  />
                </div>
                <button 
                  onClick={() => removePaper(paper.id)}
                  className="p-2 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Global Controls */}
        <section className="pt-6 border-t border-slate-800 space-y-3">
            <button 
              onClick={resetToDefault}
              className="w-full flex items-center justify-center gap-2 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-bold uppercase tracking-widest transition-all"
            >
              <RotateCcw size={14} /> Reset to Default
            </button>
        </section>
      </div>

      <div className="p-6 bg-black/40 border-t border-slate-800 text-[10px] text-physics-muted italic text-center">
        Changes are automatically saved to local storage.
      </div>
    </div>
  );
};
