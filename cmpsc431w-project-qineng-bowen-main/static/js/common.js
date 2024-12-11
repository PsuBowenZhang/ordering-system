function showToast(message) {
    $(".toast-body").text(message); // Toast content
    $(".toast").toast({ delay: 5000 }); // Set the automatic shutoff time
    $(".toast").toast("show"); // show Toast
}


// set Cookie
    function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/';
}

// get Cookie
function getCookie(name) {
    return document.cookie.split('; ').reduce((r, v) => {
        const parts = v.split('=');
        return parts[0] === name ? decodeURIComponent(parts[1]) : r;
    }, '');
}

// del Cookie
function deleteCookie(name) {
    setCookie(name, '', -1);
}