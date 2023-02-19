/**
 * Display message
 */

function showMessage(message, category="message", created_at=Date.now()) {
    // Insert new toast
    const html = document.querySelector("#message-toast").content.cloneNode(true);
    html.classList += " " + category;
    html.querySelector(".message").innerHTML = message;
    html.querySelector("time.created-at").setAttribute("datetime", created_at);
    ago = moment(created_at).fromNow();
    html.querySelector("time.created-at").append(ago);
    document.querySelector("#messages").append(html);

    // Get the last inserted toast - the one we just appended
    // and show it with bootsrap api
    const toasts = document.querySelectorAll("#messages .toast");
    const element = toasts[toasts.length-1];

    let toast_options = {
        'delay': 10000,
        'autohide': false,
    };
    // Handle toast differenlty depending on category
    switch(category) {
        case "error":
            element.classList += " bg-danger text-white"
            toast_options['autohide'] = false;
            break;
        case "success":
            element.classList += " bg-success text-white"
            toast_options['autohide'] = true;
        default:
            break;
    }

    const toast = new bootstrap.Toast(element, toast_options);
    toast.show();
}

/**
 * When page is loaded, display notifications.
 */
 window.addEventListener('load', function() {
    // Populate notifications from the page first
    let delay = 0;
    notifications.forEach(msg => {
        // Use delay as timeout to make them appear neatly.
        setTimeout(() => showMessage(msg.message, msg.category, msg.created_at), delay += 150);
    });

    // Start timed loop to fetch new notifications from backend
    setInterval(() => {
        delay = 0;
        // Fetch notifications from backend
        fetch(NOTIFICATION_URL)
            .then(response => response.json())
            .then(data => {
                data['notifications'].forEach(msg => {
                    setTimeout(() => showMessage(msg.message, msg.category, msg.created_at), delay += 150);
                });
            });
    }, NOTIFICATION_WAIT_TIME);

})

