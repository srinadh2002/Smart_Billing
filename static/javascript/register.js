let btnClear = document.querySelector('button')
let inputs = document.querySelector('input')

btnClear.addEventListener('click', () => {
    inputs.forEach(input => input.value='' );
});
