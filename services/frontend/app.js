const $ = (id) => document.getElementById(id);
async function api(path, options = {}) {
  const response = await fetch('/api/' + path, options);
  if (!response.ok) throw new Error('Service unavailable or invalid request. Please retry.');
  return response.json();
}
async function refresh() {
  try {
    const [tasks, summary] = await Promise.all([api('tasks'), api('summary')]);
    for (const key of ['total', 'completed', 'pending']) $(key).textContent = summary[key];
    $('tasks').replaceChildren();
    for (const task of tasks) {
      const li = document.createElement('li');
      const label = document.createElement('label');
      const check = document.createElement('input');
      check.type = 'checkbox'; check.checked = task.completed;
      const text = document.createElement('span'); text.textContent = task.title;
      if (task.completed) text.classList.add('done');
      check.addEventListener('change', async () => {
        check.disabled = true;
        try { await api('tasks/' + task.id, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({completed: check.checked})}); await refresh(); }
        catch (e) { check.checked = !check.checked; $('status').textContent = e.message; }
        finally { check.disabled = false; }
      });
      label.append(check, text); li.append(label); $('tasks').append(li);
    }
    $('status').textContent = tasks.length ? '' : 'No tasks yet. Add your first deployment step.';
  } catch (e) { $('status').textContent = e.message; }
}
$('task-form').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = event.target.querySelector('button'); button.disabled = true;
  try { await api('tasks', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({title: $('title').value})}); $('title').value = ''; await refresh(); }
  catch (e) { $('status').textContent = e.message; }
  finally { button.disabled = false; }
});
$('refresh').addEventListener('click', refresh);
refresh();
