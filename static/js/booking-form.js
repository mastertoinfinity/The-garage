const vehicleType = document.querySelector('#id_vehicle_type');
const carTypeSelect = document.querySelector('#id_car_type');
const carTypeField = document.querySelector('.car-type-field');

if (vehicleType && carTypeSelect && carTypeField) {
  const updateCarTypeField = () => {
    const isCar = vehicleType.value === 'car';
    carTypeField.hidden = !isCar;
    carTypeSelect.disabled = !isCar;
    if (!isCar) carTypeSelect.value = '';
  };

  vehicleType.addEventListener('change', updateCarTypeField);
  updateCarTypeField();
}