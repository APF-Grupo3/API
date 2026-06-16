console.log("addEventListener");
window.addEventListener("message", onPostMessageReceived, false);

console.log("say hello to " + lmsHost);
window.parent.postMessage({ type: "integration:hello" }, lmsHost + "/*");

function onPostMessageReceived (evt) {
  // Do some basic message validation.
  const fromTrustedHost =
    evt.origin === window.__lmsHost || evt.origin === lmsHost;

  if (!fromTrustedHost || !evt.data || !evt.data.type) {
    return;
  }

  // (2) A majority of the communication between the integration and Learn
  // Ultra will be over a "secure" MessageChannel.
  // As response to the integration handshake, Learn Ultra will send a
  // MessageChannel port to the integration.
  if (evt.data.type === "integration:hello") {
    // Store the MessageChannel port for future use
    messageChannel = new LoggedMessageChannel(evt.ports[0]);
    messageChannel.onmessage = onMessageFromUltra;

    // (3) Now, we need to authorize with Learn Ultra using the OAuth2 token
    // that the server negotiated for us
    messageChannel.postMessage({
      type: "authorization:authorize",

      // Your OAuth 2.0 REST token
      token: token,
    });
  }
}

function onMessageFromUltra (message) {
  // (4) If our authorization token was valid, Learn Ultra will send us a
  // response, notifying us that the authorization
  // was successful
  console.log("[UEF SMW MSG]", message.data);

  if (message.data.type === "authorization:authorize") {
    onAuthorizedWithUltra();
  }

  if (message.data.type === "proctoring-service:register") {
    // This is UEF responding to your message. A status will be included as well as an error if something went wrong
    console.log("[SMOWL] ProctReg", message.data.proctoringPlacementHandle);
    console.log("[SMOWL] ProctReg", message.data.status);
    console.log("[SMOWL] ProctReg", message.data.errorMessage);
  }

  if (message.data.type === "proctoring-service:settings-saved") {
    // Settings were saved for this contentId
    console.log("[SMOWL] ProctSetSaved", message.data);

    enableProctoring(
      message.data.courseUuid,
      message.data.contentId,
      message.data.enabled
    ).then(() => {
      // Your response back to UEF after you have done what you need to
      messageChannel.postMessage({
        type: "proctoring-service:settings-saved:response",
        correlationId: message.data.correlationId,
        success: true,
        error: undefined,
      });
    }).catch((error) => {
      messageChannel.postMessage({
        type: "proctoring-service:settings-saved:response",
        correlationId: message.data.correlationId,
        success: false,
        error: error.message,
      });
    });
  }

  if (message.data.type === "event:event") {
    // The event type is a new portal
    if (message.data.eventType === "portal:new") {
      // Name of the portal in view
      console.log(message.data.selector);

      // ID of portal in view
      console.log(message.data.portalId);

      // Any specific data relavant to this portal
      console.log(message.data.selectorData);

      if (
        message.data.selector ===
        "course.content.assessment.settings.proctoring.panel.settings"
      ) {
        // ID of this portal. This must be sent back to UEF in the portal:render message
        const portalId = message.data.portalId;

        // contentId is included for convience in the selectorData
        console.log(message.data.selectorData.contentId);

        const contentsToSend = {
          tag: "div",
          children: [
            {
              tag: "img",
              props: {
                alt: "Smowl Proctoring",
                src: "https://lti-smowl-global.smowltech.net/lti-app/img/buho.png", //To change on production
                height: 24,
                style: {
                  marginRight: "10px",
                },
              },
            },
            {
              tag: "span",
              children: `Smowl Proctoring Enabled`,
            },
          ],
        };

        // Send message to UEF to render this content
        messageChannel.postMessage({
          type: "portal:render",
          portalId: portalId,
          contents: contentsToSend,
        });
      }
    }
  }

  // JS INJECTION
  if (message.data.type === "injectjs:inject:response") {
    console.log("[SMOWL] JS inject response", message);
    if (message.data.status && message.data.status === "success") {
      console.log("[SMOWL] JS injected successfully");
    }
    else {
      console.log("[SMOWL] JS injection failed");
    }
  }
}

function onAuthorizedWithUltra () {
  console.log("Authorization was successful");

  // (5) Once we are authorized, we can subscribe to events, such as telemetry
  // events
  messageChannel.postMessage({
    type: "event:subscribe",
    subscriptions: [
      "click",
      "route",
      "route:changing",
      "portal:new",
      "portal:remove",
    ],
  });

  messageChannel.postMessage({
    type: "proctoring-service:register",
    proctoringPlacementHandle: proctoringPlacement,
  });

  const smowlCornerUrl = new URL(window.location.origin + "/lti-app/js/blackboard/smowl_corner.js");
  smowlCornerUrl.searchParams.append("placementId", proctoringPlacement);
  smowlCornerUrl.searchParams.append("entityName", entityName);
  smowlCornerUrl.searchParams.append("userId", userId);
  smowlCornerUrl.searchParams.append("smowlLtiAppHost", smowlLtiAppHost);

  messageChannel.postMessage({
    type: "injectjs:inject",
    url: smowlCornerUrl.toString(),
  })

}

/**
 * A MessageChannel-compatible API, but with console logging.
 */
class LoggedMessageChannel {
  onmessage = () => {
    console.log("[SMOWL] test");
  };

  constructor(messageChannel) {
    this.messageChannel = messageChannel;
    this.messageChannel.onmessage = this.onMessage;
  }

  onMessage = (evt) => {
    console.log(`[SMOWL] From Learn Ultra:`, evt.data);
    this.onmessage(evt);
  };

  postMessage = (message) => {
    console.log(`[SMOWL] To Learn Ultra`, message);
    this.messageChannel.postMessage(message);
  };
}

function enableProctoring (courseId, contentId, enabled) {
  return new Promise((resolve, reject) => {
    if (!smowlLtiAppHost || !clientId || !deploymentId || !lmsHost || !platformName) {
      reject(new Error("Missing required parameters"));
      return;
    }

    var xhr = new XMLHttpRequest();
    var url = smowlLtiAppHost + "/lti/bb/toggle-proctoring";
    xhr.open("POST", url, true); // true makes it asynchronous
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.responseText);
      } else {
        reject(new Error(`Request failed with status: ${xhr.status}`));
      }
    };

    xhr.onerror = function () {
      reject(new Error("Network error"));
    };

    xhr.send(
      JSON.stringify({
        courseId: courseId,
        contentId: contentId,
        enabled: enabled,
        clientId: clientId,
        deploymentId: deploymentId,
        lmsHost: lmsHost,
        platformName: platformName,
      })
    );
  });
}