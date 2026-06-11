import { create } from 'zustand';
import { apiGet, apiPost } from '../api/client';

export type Project = {
  id: string;
  slug: string;
  name: string;
};

type ProjectState = {
  projects: Project[];
  selectedProjectId: string | null;
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  createProject: (slug: string, name: string) => Promise<Project | null>;
  selectProject: (projectId: string | null) => void;
  getSelectedProject: () => Project | null;
};

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  selectedProjectId: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const projects = await apiGet<Project[]>('/projects');
      const { selectedProjectId } = get();
      const stillValid = projects.some((p) => p.id === selectedProjectId);
      set({
        projects,
        loading: false,
        selectedProjectId: stillValid
          ? selectedProjectId
          : projects[0]?.id ?? null,
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  createProject: async (slug, name) => {
    set({ loading: true, error: null });
    try {
      const project = await apiPost<Project>('/projects', { slug, name });
      set((state) => ({
        projects: [...state.projects, project],
        selectedProjectId: project.id,
        loading: false,
      }));
      return project;
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
      });
      return null;
    }
  },

  selectProject: (projectId) => set({ selectedProjectId: projectId }),

  getSelectedProject: () => {
    const { projects, selectedProjectId } = get();
    return projects.find((p) => p.id === selectedProjectId) ?? null;
  },
}));