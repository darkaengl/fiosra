export interface CourseAssignment {
  title: string;
  description: string;
  primary_sources?: string[];
}

export interface CourseModule {
  position: number;
  title: string;
  description: string;
  learning_objectives: string[];
  knowledge_components?: string[];
  suggested_assignments?: CourseAssignment[];
  change_status?: 'added' | 'modified' | string;
}

export interface CourseDraft {
  course_id?: string;
  title: string;
  domain: string;
  target_audience: string;
  overview: string;
  modules: CourseModule[];
}

export interface RevisionTurn {
  role: 'user' | 'assistant';
  content: string;
}
