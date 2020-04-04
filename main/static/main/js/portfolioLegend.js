function initializeLegend() {
    $('#legend').css('top', '65px')
    $(window).on('scroll',manageLegendHeight);

    $(document).ready(function() {
        $(this).scrollTop(0);
    })
}

function manageLegendHeight(e) {
    const scrollTop = $(document).scrollTop()
    
    if (scrollTop > 68) {
        $('#legend').css('top', '-3px');
    } else {
        const newTop = 65 - scrollTop;        
        $('#legend').css('top', String(newTop).concat('px'));
    }
}