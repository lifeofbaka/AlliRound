
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('form');
    const spinner = document.getElementById('spinner');
    
    // Debugging logs
    console.log('Form element:', form);
    console.log('Spinner element:', spinner);

    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission

            // Show the spinner
            if (spinner) {
                console.log('Displaying spinner...');
                spinner.classList.add('show'); // Use class to show spinner
            } else {
                console.error('Spinner element not found');
                return;
            }

            // Get CSRF token from the form
            const csrfTokenElement = form.querySelector('input[name="csrfmiddlewaretoken"]');
            console.log('CSRF token element:', csrfTokenElement);

            if (!csrfTokenElement) {
                console.error('CSRF token not found in form');
                return;
            }

            const csrfToken = csrfTokenElement.value;
            console.log('CSRF token value:', csrfToken);

            // Prepare form data
            const formData = new FormData(form);
            console.log('Form data:', Array.from(formData.entries()));

            // Send AJAX request
            fetch(form.action, {
                method: form.method,
                headers: {
                    'X-CSRFToken': csrfToken, // Include CSRF token in the header
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text(); // Get response as text
            })
            .then(html => {
                console.log('HTML response received');
                // Inject HTML response into the page
                document.open();
                document.write(html);
                document.close();
            })
            .finally(() => {
                // Hide the spinner
                if (spinner) {
                    console.log('Hiding spinner...');
                    spinner.classList.remove('show'); // Use class to hide spinner
                }
            })
            .catch(error => {
                console.error('Fetch error:', error); // Debug line
            });
        });
    } else {
        console.error('Form element not found'); // Debug line
    }
});
