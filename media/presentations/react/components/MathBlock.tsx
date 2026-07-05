import React from 'react';
import { InlineMath, BlockMath } from 'react-katex';

export const MathBlock: React.FC<{ math: string; block?: boolean }> = ({ math, block }) => {
  if (block) {
    return <div className="my-4 overflow-x-auto"><BlockMath math={math} /></div>;
  }
  return <InlineMath math={math} />;
};
