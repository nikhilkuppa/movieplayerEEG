document.addEventListener('DOMContentLoaded', function () {
    const videoPlayer = document.getElementById('videoPlayer');
    const placeholder = document.getElementById('placeholder');
    const metadataContainer = document.getElementById('metadata-table');
    const introContainer = document.getElementById('intro');
    const dropdown = document.getElementById('dropdown');
    const timeWindowInput = document.getElementById('timeWindowInput');
    const updateWindowButton = document.getElementById('updateWindowButton');
    const arrowLeft = document.getElementById('arrow-left');  // Left arrow button
    const arrowRight = document.getElementById('arrow-right'); // Right arrow button
    
    let movieName = '';
    let scenes = [];
    let currentSceneIndex = 0;
    let plot = null;
    let timeWindow = 30;  // 30 minutes window
    let currentSceneData = null;
    let plotStart = 0;
    let plotEnd = timeWindow;

    // Fetch movie list and populate dropdown
    fetch('/api/movies')
        .then(response => response.json())
        .then(movies => {
            console.log(movies);

            // Populate dropdown
            dropdown.innerHTML = `
                <option value="" selected disabled>Select a Movie</option>
                ${movies.map(movie => `
                    <option value="${movie.stimuli_id}" 
                            data-intro="${movie.Intro}" 
                            data-rt="${movie.RT_Tomatometer}" 
                            data-studio="${movie.studio}" 
                            data-imdb="${movie.iMDB}" 
                            data-year="${movie.Year}" 
                            data-grossww="${movie.gross_worldwide}" 
                            data-openingweekend="${movie.openingweekend}" 
                            data-budget="${movie.budget}">
                        ${movie.stimuli_title}
                    </option>
                `).join('')}
            `;


            // Add event listener for dropdown change
            dropdown.addEventListener('change', function () {
                const selectedStimuliId = this.value;
                if (selectedStimuliId) {
                    movieName = this.options[this.selectedIndex].text;
                    const introText = this.options[this.selectedIndex].dataset.intro;
                    const rt = this.options[this.selectedIndex].dataset.rt;
                    const studio = this.options[this.selectedIndex].dataset.studio;
                    const imdb = this.options[this.selectedIndex].dataset.imdb;
                    const year = this.options[this.selectedIndex].dataset.year;
                    const grossww = this.options[this.selectedIndex].dataset.grossww;
                    const openingweekend = this.options[this.selectedIndex].dataset.openingweekend;
                    const budget = this.options[this.selectedIndex].dataset.budget;

                    // Update intro container with a heading
                    introContainer.innerHTML = `
                        <h2 style="text-align: left; margin: 0; padding-top: 19px; font-size: 25px; ">About:</h2>
                        <p>${introText || 'No intro available'}</p>
                        <div style="display: flex; align-items: left; justify-content: left;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/5/5b/Rotten_Tomatoes.svg" alt="Rotten Tomatoes" style="width: 20px; height: 20px; margin-right: 5px;">
                            <span><b>Rotten Tomatoes:</b> ${rt || 'N/A'}<br></span>
                        </div>
                        <div style="display: flex; align-items: left; justify-content: left; margin-top: 5px; ">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/6/69/IMDB_Logo_2016.svg" alt="IMDb" style="width: 20px; height: 20px; margin-right: 5px;">
                            <span><b>IMDb:</b> ${imdb || 'N/A'}</span>
                        </div>
                        <p><b>Year of Release:</b> ${year || 'N/A'}</p>
                        <p><b>Studio:</b> ${studio || 'N/A'}</p>
                        <p><b>Budget:</b> ${budget || 'N/A'}</p>
                        <p><b>Opening Weekend (US & Canada):</b> ${openingweekend || 'N/A'}</p>
                        <p><b>Worldwide Gross:</b> $ ${grossww || 'N/A'}</p>
                        

                    `;

                    // Fetch scenes for the selected movie
                    fetch(`/api/scenes?stimuli_id=${selectedStimuliId}`)
                        .then(response => response.json())
                        .then(data => {
                            scenes = data;
                            currentSceneIndex = 0;

                            // Load the full plot and set zoom to show a 30 minutes window
                            loadFullPlot();
                            updatePlot(currentSceneIndex);
                            playNextScene(currentSceneIndex);
                        });
                }
            });
        })
        .catch(error => console.error('Error fetching movies:', error));

    function loadFullPlot() {
        const sceneStarts = scenes.map(scene => scene.scene_start / 60);
        const sceneEnds = scenes.map(scene => scene.scene_end / 60);
        const sceneDurations = scenes.map(scene => scene.scene_duration / 60);
        const eegValues = scenes.map(scene => scene.ISC_EEG);
        const midpoints = sceneStarts.map((start, index) => (start + sceneEnds[index]) / 2); // Midpoint in minutes

        const avgBaseline = eegValues.reduce((sum, value) => sum + value, 0) / eegValues.length;

        const plotData = {
            x: midpoints,
            y: eegValues,
            type: 'bar',
            text: eegValues.map(value => value.toFixed(2)),
            textposition: 'inside',
            marker: { color: 'rgba(255, 217, 0, 0.952)', line: { color: 'black', width: 1 } },
            width: sceneDurations,  // Bar widths based on scene durations
            name: 'EEG ISC',
            hoverinfo: 'x+y'
        };

        const baselineData = {
            x: [Math.min(...sceneStarts), Math.max(...sceneEnds)], // X values spanning the full range of the plot
            y: [avgBaseline, avgBaseline], // Y values set to the average baseline
            type: 'scatter',
            mode: 'lines',
            line: { color: '#B81E30', width: 2, dash: 'dashdot' },
            name: 'Average Baseline',
            hoverinfo: 'none'
        };

        const layout = {
            title: {
                text: `ISC_EEG over scenes from ${movieName.replace(/ +$/g, '')}`,
                font: { color: 'white' },
                family: "Libre Baskerville"
            },
            xaxis: {
                title: { text: 'Time (mins)', font: { color: 'white' } },
                tickfont: { color: 'white' },
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.2)',
                family: "Libre Baskerville"
            },
            yaxis: {
                title: { text: 'ISC_EEG', font: { color: 'white' } },
                tickfont: { color: 'white' },
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.2)',
                family: "Libre Baskerville"
            },
            plot_bgcolor: 'rgb(0, 0, 0)',
            paper_bgcolor: 'rgb(0, 0, 0)',
            font: { color: 'white', family: "Helvetica" }
        };

        Plotly.newPlot('plot', [plotData, baselineData], layout).then(gd => {
            plot = gd;

            // Add event listener for clicking on a scene in the plot
            gd.on('plotly_click', function (data) {
                if (data.points.length > 0) {
                    const clickedIndex = data.points[0].pointIndex;
                    currentSceneIndex = clickedIndex;
                    playNextScene(clickedIndex);
                }
            });

            // Add event listener for hovering over a scene in the plot
            gd.on('plotly_hover', function (data) {
                if (data.points.length > 0) {
                    const hoveredIndex = data.points[0].pointIndex;
                    updateMetadataDisplay(scenes[hoveredIndex]);
                }
            });

            // Add event listener for unhovering from the plot
            gd.on('plotly_unhover', function () {
                if (currentSceneData) {
                    updateMetadataDisplay(currentSceneData);
                }
            });
        });

        // Set zoom window to a 30 minutes time window initially
        const minTime = Math.min(...sceneStarts);
        const maxTime = Math.max(...sceneEnds);
        setZoomWindow(minTime, Math.min(minTime + timeWindow, maxTime));
    }

    function updatePlot(currentSceneIndex) {
        const sceneData = scenes[currentSceneIndex];
        let startTime = sceneData.scene_start / 60;
        let endTime = sceneData.scene_end / 60;

        let windowStart = Math.max(startTime - timeWindow / 2, Math.min(...scenes.map(scene => scene.scene_start / 60)));
        let windowEnd = Math.min(startTime + timeWindow / 2, Math.max(...scenes.map(scene => scene.scene_end / 60)));

        setZoomWindow(windowStart, windowEnd);
        updatePlotHighlight(currentSceneIndex);
    }

    function setZoomWindow(startTime, endTime) {
        Plotly.relayout('plot', {
            'xaxis.range': [startTime, endTime]
        });
    }

    function playScene(index) {
        const sceneData = scenes[index];
        currentSceneData = sceneData; // Update current scene data
        const formattedMovieName = movieName.replace(/ /g, '_').replace(/_+$/, '');
        videoPlayer.src = `/mp4/${formattedMovieName}_scene_${formatSceneNo(sceneData.scene_no)}_tc.mp4`;
        videoPlayer.currentTime = 0;
        placeholder.style.display = 'none';
        videoPlayer.style.display = 'block';
        videoPlayer.play();
        updateMetadataDisplay(sceneData);
        updatePlot(index);

        videoPlayer.addEventListener('ended', () => {
            videoPlayer.style.display = 'none';
            placeholder.style.display = 'block';
        })
    }

    function updateMetadataDisplay(sceneData) {
        const metadata = JSON.parse(sceneData.metadata);
        metadataContainer.innerHTML = `
            <table class="metadata-table">
                <tr>
                    <th colspan="2" style="font-size: 22px;">${movieName} - Scene ${formatSceneNo(sceneData.scene_no)}</th>
                </tr>
                ${Object.entries(metadata).map(([key, value]) => `
                    <tr>
                        <th>${key}</th>
                        <td>${value}</td>
                    </tr>
                `).join('')}
            </table>
        `;
    }

    function playNextScene(index) {
        if (index < scenes.length) {
            playScene(index);

            videoPlayer.addEventListener('ended', function onEnded() {
                videoPlayer.removeEventListener('ended', onEnded);
                currentSceneIndex++;
                playNextScene(currentSceneIndex);
            });
        }
    }

    function updatePlotHighlight(currentIndex) {
        const colors = scenes.map((_, index) => index === currentIndex ? 'rgba(66, 49, 17, 0.973)' : 'rgba(250, 166, 10, 0.884)');
        Plotly.restyle('plot', { 'marker.color': [colors] });
    }

    function formatSceneNo(sceneNo) {
        return sceneNo.toString().padStart(2, '0');
    }

    function goToPreviousView() {
        if (plotStart > 0) {
            plotEnd = plotStart;
            plotStart = Math.max(plotStart - timeWindow, 0);
            setZoomWindow(plotStart, plotEnd);
        }
    }

    function goToNextView() {
        if (plotEnd < Math.max(...scenes.map(scene => scene.scene_end / 60))) {
            plotStart = plotEnd;
            plotEnd = Math.min(plotStart + timeWindow, Math.max(...scenes.map(scene => scene.scene_end / 60)));
            setZoomWindow(plotStart, plotEnd);
        }
    }

    arrowLeft.addEventListener('click', goToPreviousView);
    arrowRight.addEventListener('click', goToNextView);

    updateWindowButton.addEventListener('click', function () {
        timeWindow = parseInt(timeWindowInput.value, 10);
        setZoomWindow(plotStart, Math.min(plotStart + timeWindow, Math.max(...scenes.map(scene => scene.scene_end / 60))));
    });
});
