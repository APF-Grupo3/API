(function () {
    const CORNER_ELEMENT_ID = "smowl-corner-container";
    const CORNER_URL_STORAGE_KEY = "smowl-corner-url";
    const ACTIVITY_URL_STORAGE_KEY = "smowl-corner-activity-url";
    const CHECK_URL_INTERVAL_MS = 2000;
    const REFRESH_PROCTORED_ACTIVITIES_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
    // Get placementId from the query string of the current script
    const javascriptUrl = new URL(document.currentScript.src);
    const urlParams = new URLSearchParams(javascriptUrl.search);
    const placementId = urlParams.get('placementId');
    const entityName = urlParams.get('entityName');
    const smowlLtiAppHost = urlParams.get('smowlLtiAppHost');
    const userId = urlParams.get('userId');
    // Load corner url from local storage
    let activityUrl = localStorage.getItem(ACTIVITY_URL_STORAGE_KEY);
    let cornerUrl = localStorage.getItem(CORNER_URL_STORAGE_KEY);
    let inExam = false;

    function startListeningMessages () {
        window.addEventListener('message', async function (event) {
            const data = event.data;
            if (data.placementId !== placementId) {
                return;
            }
            switch (data.action) {
                case 'CHECK_BLACKBOARD_JS_INJECTION':
                    sendJsEnabledMessageToLTI();
                    break;

                case "START_PROCTORING":
                    appendCorner(CORNER_ELEMENT_ID, data.url);
                    break;

                case "END_PROCTORING":
                    removeCorner(CORNER_ELEMENT_ID);
                    break;
            }
        });
    }

    function sendJsEnabledMessageToLTI () {
        const previewIframe = document.getElementById('preview-iframe');
        let doc = document;
        if (previewIframe) {
            doc = previewIframe.contentWindow.document;
        }
        ltiIframe = doc.getElementById('lti-launch-iframe');

        if (ltiIframe && ltiIframe.contentWindow) {
            ltiIframe.contentWindow.postMessage({
                type: "JS_TO_LTI",
                action: "BLACKBOARD_JS_INJECTION_ENABLED",
                placementId: placementId
            }, '*');
        } else {
            console.error('No iframe found or iframe contentWindow is not accessible');
        }
    }

    async function appendCorner (cornerId, url) {
        await examPageLoaded();
        //if corner exists do nothing
        if (document.getElementById(cornerId)) return;

        const draggingButtonClass = "dragging-button";
        const body = document.getElementsByTagName("body")[0];
        const corner = document.createElement("div");
        corner.style.position = "fixed";
        corner.style.top = "0";
        corner.style.right = "0";
        corner.style.zIndex = "999999";
        corner.id = cornerId;
        cornerUrl = url;

        saveCornerStatusInfo();

        corner.innerHTML = `<div class="${draggingButtonClass}" 
    style="position: absolute; cursor: move; width: 3.375rem; height: 2.1875rem; background-repeat: no-repeat; background-position: .75rem center; background-size: auto 40%;">
  </div>
    <iframe 
        allow="microphone; camera" 
        sandbox="allow-top-navigation allow-scripts allow-modals
        allow-same-origin allow-popups allow-downloads" 
        width="220" height="300" 
        frameborder="0" allowfullscreen scrolling="no"
        src="${cornerUrl}"
    ></iframe>`;
        body.appendChild(corner);

        makeCornerDraggable(cornerId, draggingButtonClass);

        return true;
    }

    function examPageLoaded () {
        return new Promise((resolve) => {
            const interval = setInterval(() => {
                if (window.location.href.includes('/proctoring/attempt')) {
                    clearInterval(interval);
                    inExam = true;
                    resolve();
                }
            }, 100);
        });
    }

    function saveCornerStatusInfo () {
        // save url in local storage
        localStorage.setItem(CORNER_URL_STORAGE_KEY, cornerUrl);
        // save document top url in local storage
        activityUrl = document.location.href;
        localStorage.setItem(ACTIVITY_URL_STORAGE_KEY, activityUrl);
    }

    function removeCorner (cornerId) {
        const container = document.getElementById(cornerId);
        if (container) {
            container.remove();
        }
    }

    function makeCornerDraggable (cornerId, draggingButtonClass) {
        const cornerElement = document.getElementById(cornerId);
        const draggingButton = document.getElementsByClassName(draggingButtonClass)[0];
        if (!cornerElement || !draggingButton) return;

        const draggingIndicatorImgUrl = 'https://media.smowltech.net/svg/drag-indicator.svg';
        draggingButton.style.backgroundImage = `url(${draggingIndicatorImgUrl})`;

        draggingButton.onmousedown = function (e) {
            dragMouseDown(e, cornerElement);
        };
    }

    function dragMouseDown (e, dragElement) {
        e.preventDefault();
        e.stopPropagation();
        let dragElementX = 0;
        let dragElementY = 0;
        if (dragElement.style.transform) {
            dragElementX = dragElement.style.transform.split('(')[1].split('px')[0] || 0;
            dragElementY = dragElement.style.transform.split(',')[1].split('px')[0] || 0;
        }
        const mouseDownX = e.clientX;
        const mouseDownY = e.clientY;
        document.onmouseup = () => closeDragElement(dragElement);
        // call a function whenever the cursor moves:
        document.onmousemove = elementDrag;

        let ldt = 0;
        function elementDrag (e) {
            e.preventDefault();
            e.stopPropagation();
            // We transform only if the time between the last drag is greater than 15ms
            const time = new Date().getTime()
            if (time - ldt > 15) {
                ldt = time
            }
            else {
                return;
            }
            // calculate the new cursor position:
            const mouseMoveX = e.clientX;
            const mouseMoveY = e.clientY;
            // set the element's new position:
            const x = parseInt(dragElementX) + (mouseMoveX - mouseDownX);
            const y = parseInt(dragElementY) + (mouseMoveY - mouseDownY);
            dragElement.style.webkitTransform =
                dragElement.style.transform =
                'translate(' + x + 'px, ' + y + 'px)';
        }

        function closeDragElement (dragElement) {
            // stop moving when mouse button is released:
            document.onmouseup = null;
            document.onmousemove = null;
            // Check if dragElement is out of the screen and move it back
            const rect = dragElement.getBoundingClientRect();
            const x = rect.x;
            const y = rect.y;
            const width = rect.width;
            const height = rect.height;
            const screenWidth = window.innerWidth;
            const screenHeight = window.innerHeight;
            let dragElementX = 0;
            let dragElementY = 0;
            if (dragElement.style.transform) {
                dragElementX = dragElement.style.transform.split('(')[1].split('px')[0] || 0;
                dragElementY = dragElement.style.transform.split(',')[1].split('px')[0] || 0;
            }
            let xTrans = parseInt(dragElementX);
            let yTrans = parseInt(dragElementY);
            if (x < 0) {
                xTrans = xTrans - x;
            }
            if (x + width > screenWidth) {
                xTrans = xTrans - (x + width - screenWidth);
            }
            if (y < 0) {
                yTrans = yTrans - y;
            }
            if (y + height > screenHeight) {
                yTrans = yTrans - (y + height - screenHeight);
            }
            dragElement.style.webkitTransform =
                dragElement.style.transform =
                'translate(' + xTrans + 'px, ' + yTrans + 'px)';
        }
    }

    function tryToRecoverCorner () {
        if (cornerUrl && activityUrl === document.location.href) {
            appendCorner(CORNER_ELEMENT_ID, cornerUrl);
        } else if (inExam) {
            inExam = false;
            removeCorner(CORNER_ELEMENT_ID);
        }
    }

    function startUrlCheckInterval () {
        tryToRecoverCorner();
        // Interval to check if the url has changed and remove or append the smowl corner
        setInterval(() => {
            tryToRecoverCorner();
        }, CHECK_URL_INTERVAL_MS);
    }

    function listenPageLoadedEvents () {
        checkUserSpelledOut(window.location.href).then(spelledOut => {
            if (spelledOut) showSpelledOutMessage();
        });
    }


    async function checkUserSpelledOut (url) {

        if (!isInExamPage(url)) {
            return false;
        }
        let activityId = getActivityIdFromUrl(url);
        activityId = 'test' + activityId.replaceAll('_', 'usmwl')

        const apiUrl = new URL(smowlLtiAppHost + `/smowl-oapi/entity/${entityName}/activity/${activityId}/user/${userId}/spelled-out`);

        try {
            const response = await fetch(apiUrl.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            /**
             * Expected response format:
             * {
             *   "spelledOut": true/false
             * }
             */
            const result = await response.json();

            return result.spelledOut === true;
        } catch (error) {
            console.error("Error fetching user spelled out status:", error);
            return false;
        }
    }


    function getLanguageCode () {
        const lang = document.documentElement.lang || 'en';
        const langCode = lang.split('-')[0]; // Get the first part before '-'
        return langCode;
    }

    function showSpelledOutMessage () {
        if (getLanguageCode() === 'es' || getLanguageCode() === 'ca' || getLanguageCode() === 'gl' || getLanguageCode() === 'eu') {
            alert("Has sido expulsado de la actividad debido a un comportamiento no permitido detectado por el sistema de supervisión. Si crees que esto es un error, por favor contacta con tu institución.");
        } else {
            alert("You have been expelled from the activity due to disallowed behavior detected by the monitoring system. If you believe this is an error, please contact your institution.");
        }
        // Then redirect to history back if possible
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    }

    function isInExamPage (url) {
        return url.includes('/proctoring/attempt');
    }

    function getActivityIdFromUrl (url) {
        //https://smowltech-test.blackboard.com/ultra/courses/_129_1/outline/assessment/_432_1/proctoring/attempt?contentId=_432_1&returnToProctoringToolOnEndAssessment=true&courseId=_129_1
        const urlObj = new URL(url);
        // Return contentId param
        return urlObj.searchParams.get('contentId');
    }

    startUrlCheckInterval();

    startListeningMessages();

    listenPageLoadedEvents();
})();