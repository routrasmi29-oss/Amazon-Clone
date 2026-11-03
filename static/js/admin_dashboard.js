document.addEventListener("DOMContentLoaded", function () {

    // ================================
    // GET CHART ELEMENT
    // ================================

    const chartElement = document.getElementById("salesChart");

    if (!chartElement) {
        return;
    }


    // ================================
    // GET DATA FROM HTML
    // ================================

    let monthlyLabels = [];
    let monthlyRevenue = [];


    try {

        monthlyLabels = JSON.parse(
            chartElement.dataset.labels || "[]"
        );

    } catch (error) {

        console.error(
            "Monthly labels data error:",
            error
        );

    }


    try {

        monthlyRevenue = JSON.parse(
            chartElement.dataset.revenue || "[]"
        );

    } catch (error) {

        console.error(
            "Monthly revenue data error:",
            error
        );

    }


    // ================================
    // CREATE CHART
    // ================================

    const ctx = chartElement.getContext("2d");


    new Chart(ctx, {

        type: "line",


        data: {

            labels: monthlyLabels,

            datasets: [

                {

                    label: "Monthly Revenue",

                    data: monthlyRevenue,

                    borderColor: "#ff9900",

                    backgroundColor:
                        "rgba(255, 153, 0, 0.15)",

                    borderWidth: 3,

                    fill: true,

                    tension: 0.4,

                    pointBackgroundColor:
                        "#232f3e",

                    pointBorderColor:
                        "#232f3e",

                    pointRadius: 5,

                    pointHoverRadius: 7

                }

            ]

        },


        // ================================
        // CHART OPTIONS
        // ================================

        options: {

            responsive: true,

            maintainAspectRatio: false,


            plugins: {

                legend: {

                    display: true,

                    position: "top"

                },

                tooltip: {

                    callbacks: {

                        label: function (context) {

                            return " Revenue: ₹" +
                                context.parsed.y;

                        }

                    }

                }

            },


            scales: {

                x: {

                    title: {

                        display: true,

                        text: "Month"

                    }

                },


                y: {

                    beginAtZero: true,

                    title: {

                        display: true,

                        text: "Revenue"

                    },


                    ticks: {

                        callback: function (value) {

                            return "₹" + value;

                        }

                    }

                }

            }

        }

    });

});