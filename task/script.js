// Récupère les éléments du DOM
const taskInput = document.getElementById('task-input');
const timeInput = document.getElementById('time-input');
const addTaskBtn = document.getElementById('add-task-btn');
const taskList = document.getElementById('task-list');

// Ajoute un événement lorsqu'on clique sur le bouton "Ajouter"
addTaskBtn.addEventListener('click', function() {
  const taskText = taskInput.value;
  const taskTime = parseInt(timeInput.value, 10);

  if (taskText.trim() !== '' && !isNaN(taskTime)) {
    createTask(taskText, taskTime);
    taskInput.value = '';
    timeInput.value = '';
  }
});

// Ajoute un événement lorsqu'on appuie sur la touche "Entrée" dans le champ de saisie de temps
timeInput.addEventListener('keydown', function(event) {
  if (event.key === 'Enter') {
    const taskText = taskInput.value;
    const taskTime = parseInt(timeInput.value, 10);

    if (taskText.trim() !== '' && !isNaN(taskTime)) {
      createTask(taskText, taskTime);
      taskInput.value = '';
      timeInput.value = '';
    }
  }
});

// Crée une nouvelle tâche et l'ajoute à la liste des tâches
function createTask(taskText, taskTime) {
  const taskItem = document.createElement('li');
  taskItem.className = 'task-item';

  const taskTextElement = document.createElement('div');
  taskTextElement.className = 'task-text';
  taskTextElement.textContent = taskText;

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'delete-btn';
  deleteBtn.textContent = 'Supprimer';

  let timerInterval;
  let timeInSeconds = taskTime * 60;

  deleteBtn.addEventListener('click', function() {
    clearInterval(timerInterval);
    taskItem.remove();
  });

  taskItem.appendChild(taskTextElement);
  taskItem.appendChild(deleteBtn);

  taskList.appendChild(taskItem);

  startTimer();

  // Démarre le minuteur
  function startTimer() {
    timerInterval = setInterval(updateTimer, 1000);
  }

  // Met à jour le minuteur
  function updateTimer() {
    timeInSeconds--;
    const formattedTime = formatTime(timeInSeconds);
    taskTextElement.textContent = `${taskText} (${formattedTime})`;

    // Vérifie si la tâche a expiré
    if (timeInSeconds <= 0) {
      taskItem.classList.add('expired');
      playSound();
      clearInterval(timerInterval);
    }
  }

  // Joue le son
  function playSound() {
    const audio = new Audio('https://github.com/berru-g/PadMusical/raw/master/public/rsc-mp3/Sample-lofi/D1EG8%20-%20Strawberrys%20120.wav'); // Remplacez 'path/to/sound.mp3' par le chemin vers votre fichier audio
    audio.play();
  }

  // Formate le temps en minutes et secondes
  function formatTime(timeInSeconds) {
    const minutes = Math.floor(timeInSeconds / 60).toString().padStart(2, '0');
    const seconds = (timeInSeconds % 60).toString().padStart(2, '0');
    return `${minutes}:${seconds}`;
  }
}
