// =========================================================
// PODPULSE - SOCIAL MEDIA SENTIMENT ANALYSIS
// =========================================================

// Store chart instance
let sentimentChart = null;


// =========================================================
// RUN ANALYSIS
// =========================================================

async function runAnalysis() {

    // Get URL from input
    const socialUrlElement =
        document.getElementById("socialUrl") ||
        document.getElementById("youtubeUrl");

    if (!socialUrlElement) {
        alert("URL input field not found.");
        return;
    }

    const socialUrl =
        socialUrlElement.value.trim();


    // Check empty URL
    if (socialUrl === "") {

        alert(
            "Please enter a social-media URL."
        );

        return;
    }


    // Show loading
    const loading =
        document.getElementById("loading");

    if (loading) {
        loading.style.display = "block";
    }


    try {

        // =================================================
        // SEND URL TO FLASK BACKEND
        // =================================================

        const response = await fetch(
            "/api/analyze",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    url: socialUrl
                })
            }
        );


        // Convert response to JSON
        const data =
            await response.json();


        // =================================================
        // CHECK BACKEND ERROR
        // =================================================

        if (!response.ok) {

            alert(
                data.error ||
                "Unable to analyze this link."
            );

            return;
        }


        // =================================================
        // DISPLAY RESULTS
        // =================================================

        displayResults(data);

    }

    catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        alert(
            "Unable to connect to the backend. " +
            "Please make sure Flask is running."
        );

    }

    finally {

        // Hide loading
        if (loading) {
            loading.style.display = "none";
        }

    }
}


// =========================================================
// DISPLAY RESULTS
// =========================================================

function displayResults(data) {

    console.log(
        "Analysis result:",
        data
    );


    // =================================================
    // TOTAL COMMENTS
    // =================================================

    setText(
        "totalComments",
        data.totalComments
    );


    // =================================================
    // POSITIVE
    // =================================================

    setText(
        "positive",
        data.positive
    );


    setText(
        "positiveCount",
        data.positive
    );


    // =================================================
    // NEGATIVE
    // =================================================

    setText(
        "negative",
        data.negative
    );


    setText(
        "negativeCount",
        data.negative
    );


    // =================================================
    // NEUTRAL
    // =================================================

    setText(
        "neutral",
        data.neutral
    );


    setText(
        "neutralCount",
        data.neutral
    );


    // =================================================
    // SPAM
    // =================================================

    setText(
        "spam",
        data.spam
    );


    setText(
        "spamCount",
        data.spam
    );


    // =================================================
    // PLATFORM
    // =================================================

    const platformElement =
        document.getElementById(
            "platform"
        );

    if (platformElement) {

        platformElement.textContent =
            formatPlatformName(
                data.platform
            );

    }


    // =================================================
    // KEYWORDS
    // =================================================

    displayKeywords(
        data.keywords || []
    );


    // =================================================
    // COMMENTS
    // =================================================

    displayComments(
        data.comments || []
    );


    // =================================================
    // SENTIMENT CHART
    // =================================================

    createSentimentChart(
        data
    );


    // =================================================
    // SHOW RESULTS SECTION
    // =================================================

    const results =
        document.getElementById(
            "results"
        );

    if (results) {

        results.style.display =
            "block";

    }

}


// =========================================================
// SET TEXT SAFELY
// =========================================================

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.textContent =
            value ?? 0;

    }

}


// =========================================================
// FORMAT PLATFORM NAME
// =========================================================

function formatPlatformName(
    platform
) {

    if (!platform) {
        return "Unknown";
    }


    const names = {

        youtube: "YouTube",

        instagram: "Instagram",

        tiktok: "TikTok",

        facebook: "Facebook",

        twitter: "X / Twitter",

        snapchat: "Snapchat"

    };


    return names[
        platform.toLowerCase()
    ] || platform;

}


// =========================================================
// DISPLAY KEYWORDS
// =========================================================

function displayKeywords(
    keywords
) {

    const container =
        document.getElementById(
            "keywords"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !keywords ||
        keywords.length === 0
    ) {

        container.innerHTML =
            "<p>No keywords found.</p>";

        return;

    }


    keywords.forEach(
        function(item) {

            const keyword =
                document.createElement(
                    "span"
                );


            keyword.className =
                "keyword";


            keyword.textContent =
                `${item.word} (${item.count})`;


            container.appendChild(
                keyword
            );

        }
    );

}


// =========================================================
// DISPLAY COMMENTS
// =========================================================

function displayComments(
    comments
) {

    const container =
        document.getElementById(
            "comments"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !comments ||
        comments.length === 0
    ) {

        container.innerHTML =
            "<p>No comments found.</p>";

        return;

    }


    comments.forEach(
        function(item) {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "comment-card";


            // User
            const user =
                document.createElement(
                    "h4"
                );

            user.textContent =
                item.user || "Unknown";


            // Comment
            const comment =
                document.createElement(
                    "p"
                );

            comment.textContent =
                item.comment || "";


            // Sentiment
            const sentiment =
                document.createElement(
                    "span"
                );

            sentiment.className =
                "sentiment " +
                getSentimentClass(
                    item.sentiment
                );


            sentiment.textContent =
                item.sentiment || "Neutral";


            // Likes
            const likes =
                document.createElement(
                    "small"
                );

            likes.textContent =
                `Likes: ${item.likeCount || 0}`;


            card.appendChild(
                user
            );

            card.appendChild(
                comment
            );

            card.appendChild(
                sentiment
            );

            card.appendChild(
                likes
            );


            // Spam label
            if (item.spam) {

                const spam =
                    document.createElement(
                        "span"
                    );

                spam.className =
                    "spam-label";

                spam.textContent =
                    "Spam";

                card.appendChild(
                    spam
                );

            }


            container.appendChild(
                card
            );

        }
    );

}


// =========================================================
// SENTIMENT CSS CLASS
// =========================================================

function getSentimentClass(
    sentiment
) {

    if (!sentiment) {
        return "neutral";
    }


    return sentiment
        .toLowerCase();

}


// =========================================================
// CREATE SENTIMENT CHART
// =========================================================

function createSentimentChart(
    data
) {

    const canvas =
        document.getElementById(
            "sentimentChart"
        );


    if (!canvas) {
        return;
    }


    // Destroy previous chart
    if (sentimentChart) {

        sentimentChart.destroy();

    }


    // Check Chart.js
    if (
        typeof Chart ===
        "undefined"
    ) {

        console.warn(
            "Chart.js is not loaded."
        );

        return;

    }


    sentimentChart =
        new Chart(
            canvas,
            {

                type: "doughnut",

                data: {

                    labels: [
                        "Positive",
                        "Negative",
                        "Neutral",
                        "Spam"
                    ],

                    datasets: [

                        {

                            data: [

                                data.positive || 0,

                                data.negative || 0,

                                data.neutral || 0,

                                data.spam || 0

                            ]

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    plugins: {

                        legend: {

                            position:
                                "bottom"

                        }

                    }

                }

            }
        );

}


// =========================================================
// ENTER KEY SUPPORT
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        const input =
            document.getElementById(
                "socialUrl"
            ) ||
            document.getElementById(
                "youtubeUrl"
            );


        if (input) {

            input.addEventListener(
                "keypress",
                function(event) {

                    if (
                        event.key ===
                        "Enter"
                    ) {

                        runAnalysis();

                    }

                }
            );

        }

    }
);