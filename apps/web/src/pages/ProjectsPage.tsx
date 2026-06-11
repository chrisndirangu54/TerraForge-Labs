import { FormEvent, useEffect, useState } from 'react';
import { useProjectStore } from '../stores/projectStore';

export function ProjectsPage() {
  const { projects, selectedProjectId, loading, error, fetchProjects, createProject, selectProject } =
    useProjectStore();
  const [slug, setSlug] = useState('');
  const [name, setName] = useState('');

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!slug.trim() || !name.trim()) return;
    const created = await createProject(slug.trim(), name.trim());
    if (created) {
      setSlug('');
      setName('');
    }
  }

  return (
    <div>
      <h2>Projects</h2>
      <p>List and create exploration projects scoped to your TerraForge account.</p>

      <form
        onSubmit={onCreate}
        style={{
          display: 'grid',
          gap: '0.75rem',
          maxWidth: 420,
          marginBottom: '1.5rem',
          padding: '1rem',
          border: '1px solid #ddd',
          borderRadius: 6,
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1rem' }}>Create project</h3>
        <label>
          Slug
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="kitui-ta"
            style={{ width: '100%' }}
          />
        </label>
        <label>
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Kitui Ta Project"
            style={{ width: '100%' }}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Create project'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}

      <section>
        <h3 style={{ fontSize: '1rem' }}>Project list</h3>
        {loading && projects.length === 0 ? <p>Loading projects...</p> : null}
        {!loading && projects.length === 0 ? (
          <p>No projects yet. Create one above or sign in with a geologist account.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>
                  Name
                </th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>
                  Slug
                </th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>
                  Active
                </th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{project.name}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{project.slug}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    <button
                      type="button"
                      onClick={() => selectProject(project.id)}
                      disabled={selectedProjectId === project.id}
                    >
                      {selectedProjectId === project.id ? 'Selected' : 'Select'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}