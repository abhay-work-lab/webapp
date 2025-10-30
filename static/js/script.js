$(document).ready(function() {
    $("#hallSelect").on("change", function() {
        const hall = $(this).val();
        $("#boothList").html("<div class='text-muted'>Loading booths...</div>");
        $("#boothInfo").html("Loading booth details...");

        $.ajax({
            url: "/get_hall_data",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ hall }),
            success: function(data) {
                console.log("✅ Data received:", data);
                if (!data || data.length === 0) {
                    $("#boothList").html("<div class='text-danger'>No booths found for " + hall + "</div>");
                    return;
                }

                let html = "<div class='row'>";
                data.forEach((booth, idx) => {
                    html += `
                      <div class='col-md-4 mb-3'>
                        <div class='card booth-card' data-index='${idx}'>
                          <div class='card-body'>
                            <h6 class='card-title text-primary mb-1'>${booth.Company || "Unknown"}</h6>
                            <p class='card-text mb-0'><b>Booth:</b> ${booth.Booth || "N/A"}</p>
                            <p class='text-muted small'>${booth.Category || ""}</p>
                          </div>
                        </div>
                      </div>
                    `;
                });
                html += "</div>";

                $("#boothList").html(html);

                // Booth click listener
                $(".booth-card").on("click", function() {
                    const idx = $(this).data("index");
                    const booth = data[idx];
                    $("#boothInfo").html(`
                        <b>Company:</b> ${booth.Company}<br>
                        <b>Booth:</b> ${booth.Booth}<br>
                        <b>Category:</b> ${booth.Category}<br>
                        <b>Hall:</b> ${booth.Hall}
                    `);
                });
            },
            error: function(xhr, status, err) {
                console.error("❌ AJAX error:", err);
                $("#boothList").html("<div class='text-danger'>Failed to load booths.</div>");
            }
        });
    });

    // Trigger on first load
    $("#hallSelect").trigger("change");
});
