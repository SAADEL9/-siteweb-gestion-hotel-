document.addEventListener('DOMContentLoaded', function () {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');

    flatpickr(checkInInput, {
        minDate: "today",
        dateFormat: "Y-m-d",
        onChange: function (selectedDates, dateStr, instance) {
            if (selectedDates.length > 0) {
                checkOutInput._flatpickr.set('minDate', dateStr);
            }
        }
    });

    flatpickr(checkOutInput, {
        minDate: "today",
        dateFormat: "Y-m-d"
    });
});
