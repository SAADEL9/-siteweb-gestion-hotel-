document.addEventListener('DOMContentLoaded', function () {
    const checkInInput = document.getElementById('id_check_in');
    const checkOutInput = document.getElementById('id_check_out');
    const blockedDatesElement = document.getElementById('blocked-dates-json');
    let disabledDates = [];

    if (blockedDatesElement) {
        try {
            disabledDates = JSON.parse(blockedDatesElement.textContent);
        } catch (e) {
            console.error("Error parsing blocked dates:", e);
            disabledDates = [];
        }
    }

    if (checkInInput) {
        flatpickr(checkInInput, {
            minDate: "today",
            dateFormat: "Y-m-d",
            disable: disabledDates,
            onChange: function (selectedDates, dateStr, instance) {
                if (selectedDates.length > 0 && checkOutInput && checkOutInput._flatpickr) {
                    // Set minDate for checkout to be the selected check-in date
                    checkOutInput._flatpickr.set('minDate', dateStr);

                    // If the selected check-in date is the same as the check-out date,
                    // and that date was previously selected for check-out, flatpickr might clear it.
                    // We need to ensure the check-out date is after the check-in date.
                    // So, if check-out is before or same as new check-in, clear check-out.
                    const checkOutDate = checkOutInput._flatpickr.selectedDates[0];
                    if (checkOutDate && new Date(dateStr) >= checkOutDate) {
                         checkOutInput._flatpickr.clear();
                    }
                }
            }
        });
    }

    if (checkOutInput) {
        flatpickr(checkOutInput, {
            minDate: "today", // Initial minDate, will be updated by check-in's onChange
            dateFormat: "Y-m-d",
            disable: disabledDates,
            // Additional logic to ensure check-out is after check-in
            onOpen: function(selectedDates, dateStr, instance) {
                const checkInDateStr = checkInInput.value;
                if (checkInDateStr) {
                    instance.set('minDate', checkInDateStr);
                }
            }
        });
    }
});
