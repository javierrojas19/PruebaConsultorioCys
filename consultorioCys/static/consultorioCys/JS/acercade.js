// Mostrar/ocultar información adicional con efecto suave
document.getElementById('infoButton').addEventListener('click', function () {
    const extraInfo = document.getElementById('extraInfo');
    extraInfo.classList.toggle('hidden');
    if (!extraInfo.classList.contains('hidden')) {
      extraInfo.style.opacity = '0';
      setTimeout(() => (extraInfo.style.opacity = '1'), 10);
    }
  });
  