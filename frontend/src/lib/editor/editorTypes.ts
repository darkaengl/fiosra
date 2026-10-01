export type EpistemicType =
  | 'claim'
  | 'evidence'
  | 'reasoning'
  | 'assumption'
  | 'premature_closure';

export interface EpistemicConfigItem {
  label: string;
  icon: string;
  desc: string;
}

export interface EpistemicClassification {
  epistemic_type: EpistemicType;
  confidence: number;
  oracle_probe?: string;
  source_grounded?: boolean;
  targeted_vulnerability?: string;
  socratic_moves?: any[];
}

export interface SentenceItem extends EpistemicClassification {
  from: number;
  to: number;
  text: string;
}

export interface DocumentBlock {
  block_id: string;
  block_type: string;
  content: {
    type: string;
    attrs?: Record<string, any>;
    content?: any[];
  };
  plaintext: string;
  position: number;
  section_id?: string;
  author_type?: string;
}

export interface DocumentHeading {
  page: number;
  level: number;
  text: string;
  blockId: string;
}
