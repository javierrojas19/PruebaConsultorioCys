// Obtener los botones y formularios
const btnPaciente = document.getElementById('btnPaciente');
const btnDoctor = document.getElementById('btnDoctor');
const pacienteForm = document.getElementById('pacienteForm');
const doctorForm = document.getElementById('doctorForm');

// Mostrar el formulario de Paciente por defecto
pacienteForm.style.display = 'block';
doctorForm.style.display = 'none';

// Al hacer clic en Paciente, mostrar su formulario y ocultar el de Doctor
btnPaciente.addEventListener('click', () => {
  pacienteForm.style.display = 'block';
  doctorForm.style.display = 'none';
  btnPaciente.classList.add('active');
  btnDoctor.classList.remove('active');
});

// Al hacer clic en Doctor, mostrar su formulario y ocultar el de Paciente
btnDoctor.addEventListener('click', () => {
  doctorForm.style.display = 'block';
  pacienteForm.style.display = 'none';
  btnDoctor.classList.add('active');
  btnPaciente.classList.remove('active');
});

