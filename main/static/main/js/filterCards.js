var CARD_COLS
var FILTER_STATES = {}
var CACHED_SELECTION = []
/*
    filterList: An object with keys of the filter types as they'll appear in element.dataset
        and values of space delimited list of possible options
*/
function initializeCardFilters(filterList) {
    filterList = JSON.parse(filterList)
    
    $(document).ready(getAllCards())
    initializeFilterStates(filterList)
}

function getAllCards() {
    CARD_COLS = $("#cardContainer").children()
}

function initializeFilterStates(filterList) {
    for (var typeKey in filterList) {       
        typeOptions = filterList[typeKey]
        typeOptions = typeOptions.split(" ")        
        
        FILTER_STATES[typeKey] = {}

        for (var optionKey in typeOptions) {
            FILTER_STATES[typeKey][typeOptions[optionKey]] = false
        };
    };
}

/*
    filterType: data attribute as it would appear in element.dataset
    filterSelection:  the relevant attribute value to update
*/
function updateFilters(filterType, filterSelection) {
    FILTER_STATES[filterType][filterSelection] = !FILTER_STATES[filterType][filterSelection]
    updateOptionColor(filterType, filterSelection)

    if (FILTER_STATES[filterType][filterSelection]) {
        CACHED_SELECTION = [filterType, filterSelection]
        CARD_COLS.each(function (index) {
            applyNewFilterToAllRelevantElements(index)})

    } else if (noFiltersApplied()) {
        unfilter_all_cards()

    } else {
        reevaluateAllFilters()
    }
}

function updateOptionColor(filterType, filterSelection) {
    elementID = filterType.concat("-",filterSelection)
    $("#" + elementID).toggleClass('filtered')
}

function applyNewFilterToAllRelevantElements(index) {
    filterType = CACHED_SELECTION[0]
    filterSelection = CACHED_SELECTION[1]  
    
    if (!$(CARD_COLS[index]).attr(filterType).split(" ").includes(filterSelection)) {
        applyOrRemoveFilterClass(CARD_COLS[index], true)
    }
}

function unfilter_all_cards() {
    CARD_COLS.each( function (index) {
        removeFilterClass(CARD_COLS[index])
    })
}

function noFiltersApplied() {
    noFilterExists = true

    for (var filterTypeKey in FILTER_STATES) {
        for (var stateKey in FILTER_STATES[filterTypeKey]) {       

            noFilterExists = !FILTER_STATES[filterTypeKey][stateKey]
            if (!noFilterExists) {break}
        }

        if (!noFilterExists) {break}
    }

    return noFilterExists
}

function reevaluateAllFilters() {
    var cardsToShow = CARD_COLS.toArray() //Show all by default
    console.log("Reevaluate all filters");

    for (var typeKey in FILTER_STATES) {

        for (var stateKey in FILTER_STATES[typeKey]) {    
            cardsToShow = reevaluateFilter(typeKey, stateKey, cardsToShow)
        }
    }

    for (var i=0 ; i<CARD_COLS.length ; i++) {
        
        if (cardsToShow.includes(CARD_COLS[i])) {
            applyOrRemoveFilterClass(CARD_COLS[i], false)

        } else {
            applyOrRemoveFilterClass(CARD_COLS[i], true)
        }
    }
}

function reevaluateFilter(typeKey, stateKey, cardsToShow) {
    var newCardsToShow = []   
    
    if (FILTER_STATES[typeKey][stateKey]) {
        for (var index in cardsToShow) {      

            if ($(cardsToShow[index]).attr(typeKey).split(" ").includes(stateKey)) {
                newCardsToShow.push(cardsToShow[index])
            }
        }
    }

    return newCardsToShow.length>0 ? newCardsToShow : cardsToShow
}

function hideCardIfNecessary(element, typeKey, stateKey) {
    if ($(element).attr(typeKey).split(" ").includes(stateKey)) {
        applyOrRemoveFilterClass(element, true)
    }
}

function showCardIfNecessary(element, typeKey, stateKey) {
    if ($(element).attr(typeKey).split(" ").includes(stateKey)) {
        applyOrRemoveFilterClass(element, false)
    }
}

function isFiltered(typeKey, stateKey) {
    return FILTER_STATES[typeKey][stateKey]
}

function applyOrRemoveFilterClass(element, shouldFilter) {
    if (shouldFilter) {
        applyFilterClass(element)
    } else {
        removeFilterClass(element)
    }
}

function applyFilterClass(element) {
    $(element).hide(1000)
}

function removeFilterClass(element) {
    $(element).show(1000)
}