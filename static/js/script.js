function formatDate(dateStr) {
    const [year, month, day] = dateStr.split('-');
    return `${day}.${month}.${year}`;
}

// Function to set both dates to today
function setDefaultDates() {
    const today = new Date();
    const formattedToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    // Set both input fields to today's date
    document.getElementById('update_from').value = formattedToday;
    document.getElementById('update_to').value = formattedToday;
}

window.onload = setDefaultDates;

function sendUpdateRequest() {
    document.getElementById('dots-container').style.display = 'flex';
    document.getElementById('loading-message').style.display = 'block';
    document.getElementById('response-message').textContent = '';

    const update_from = document.getElementById('update_from').value;
    const update_to = document.getElementById('update_to').value;
    const formatted_update_from = formatDate(update_from);
    const formatted_update_to = formatDate(update_to);
    const data = {
        update_from: formatted_update_from,
        update_to: formatted_update_to
    };

    fetch('/update_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            document.getElementById('loading-message').style.display = 'none';
            document.getElementById('dots-container').style.display = 'none';
            const messageElement = document.getElementById('response-message');

            const urlRegex = /(https?:\/\/[^\s]+)/g;
            const messageText = result.message || result.error;
            messageElement.innerHTML = messageText.replace(urlRegex, (url) => {
                return `<a href="${url}" target="_blank">${url}</a>`;
            });
        })
        .catch(error => {
            document.getElementById('loading-message').style.display = 'none';
            document.getElementById('response-message').textContent = 'Error: ' + error;
        });
}
