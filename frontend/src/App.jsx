import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "";

async function api(path, options) {
  const res = await fetch(`${API}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.status === 204 ? null : res.json();
}

export default function App() {
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  const load = () =>
    api("/todos").then(setTodos).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const add = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      const todo = await api("/todos", {
        method: "POST",
        body: JSON.stringify({ title }),
      });
      setTodos([todo, ...todos]);
      setTitle("");
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  const toggle = async (todo) => {
    try {
      const updated = await api(`/todos/${todo.id}`, {
        method: "PATCH",
        body: JSON.stringify({ done: !todo.done }),
      });
      setTodos(todos.map((t) => (t.id === todo.id ? updated : t)));
    } catch (e) {
      setError(e.message);
    }
  };

  const remove = async (id) => {
    try {
      await api(`/todos/${id}`, { method: "DELETE" });
      setTodos(todos.filter((t) => t.id !== id));
    } catch (e) {
      setError(e.message);
    }
  };

  const remaining = todos.filter((t) => !t.done).length;

  return (
    <main className="app">
      <h1>Todo</h1>

      <form onSubmit={add} className="add">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a task"
          maxLength={200}
          aria-label="New task"
        />
        <button type="submit">Add</button>
      </form>

      {error && <p className="error">{error}</p>}

      {todos.length === 0 ? (
        <p className="empty">No tasks yet. Add one above.</p>
      ) : (
        <>
          <ul>
            {todos.map((t) => (
              <li key={t.id} className={t.done ? "done" : ""}>
                <label>
                  <input
                    type="checkbox"
                    checked={t.done}
                    onChange={() => toggle(t)}
                  />
                  <span>{t.title}</span>
                </label>
                <button
                  className="remove"
                  onClick={() => remove(t.id)}
                  aria-label={`Delete ${t.title}`}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
          <p className="count">{remaining} remaining</p>
        </>
      )}
    </main>
  );
}
