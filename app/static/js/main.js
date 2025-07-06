document.addEventListener('DOMContentLoaded', () => {
    // --- Theme Toggler ---
    const themeToggler = document.getElementById('theme-toggler');
    if (themeToggler) {
        const htmlElement = document.documentElement;
        const themeIcon = themeToggler.querySelector('i');

        const setTheme = (theme) => {
            htmlElement.setAttribute('data-bs-theme', theme);
            if (theme === 'dark') {
                themeIcon.classList.remove('bi-sun-fill');
                themeIcon.classList.add('bi-moon-stars-fill');
            } else {
                themeIcon.classList.remove('bi-moon-stars-fill');
                themeIcon.classList.add('bi-sun-fill');
            }
            localStorage.setItem('theme', theme);
        };

        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);

        themeToggler.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    // --- Import Page Logic ---
    const importWorkflow = document.getElementById('import-workflow');
    if (importWorkflow) {
        const selectStep = document.getElementById('select-step');
        const stageStep = document.getElementById('stage-step');
        const folderList = document.getElementById('folder-list');
        const folderListLoader = document.getElementById('folder-list-loader');
        const reviewBtn = document.getElementById('review-btn');
        const stageArea = document.getElementById('stage-area');
        const addAllBtn = document.getElementById('add-all-btn');
        const backBtn = document.getElementById('back-btn');

        const loadFolders = async () => {
            try {
                const response = await fetch('/api/browse-folders');
                if (!response.ok) throw new Error('Failed to fetch folders.');
                const folders = await response.json();
                folderListLoader.classList.add('d-none');
                folderList.innerHTML = '';
                if (folders.length === 0) {
                    folderList.innerHTML = '<p class="text-muted">No new folders found to import.</p>';
                } else {
                    folders.forEach(folder => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="${folder}" id="folder-${folder}">
                                <label class="form-check-label" for="folder-${folder}">
                                    ${folder}
                                </label>
                            </div>`;
                        folderList.appendChild(li);
                    });
                }
                folderList.classList.remove('d-none');
            } catch (error) {
                folderListLoader.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
            }
        };

        folderList.addEventListener('change', () => {
            const checked = folderList.querySelectorAll('input[type="checkbox"]:checked');
            reviewBtn.disabled = checked.length === 0;
        });

        reviewBtn.addEventListener('click', async () => {
            const checkedFolders = Array.from(folderList.querySelectorAll('input:checked')).map(cb => cb.value);
            reviewBtn.disabled = true;
            reviewBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Staging...';

            const response = await fetch('/api/stage-playlists', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folders: checkedFolders }),
            });
            const stagedData = await response.json();
            
            displayStagedPlaylists(stagedData);

            selectStep.classList.add('d-none');
            stageStep.classList.remove('d-none');
            reviewBtn.disabled = false;
            reviewBtn.innerHTML = '<i class="bi bi-card-checklist me-1"></i> Review Selected';
        });

        const displayStagedPlaylists = (playlists) => {
            stageArea.innerHTML = '';
            playlists.forEach(p => {
                const card = document.createElement('div');
                card.className = `card staged-card ${p.isValid ? '' : 'border-danger'}`;
                card.dataset.folderName = p.folderName;

                let validationHtml = '';
                if (!p.isValid) {
                    validationHtml = `<div class="alert alert-danger mb-3"><strong>Validation Failed:</strong><ul>${p.validationErrors.map(e => `<li>${e}</li>`).join('')}</ul></div>`;
                }

                card.innerHTML = `
                    <div class="card-body">
                        ${validationHtml}
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="title" value="${p.data.Title}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Author</label>
                            <input type="text" class="form-control" name="author" value="${p.data.Author}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="3">${p.data.Description}</textarea>
                        </div>
                        <h6>Tracks (${p.data.tracks.length})</h6>
                        <ul class="list-group">
                            ${p.data.tracks.map(t => `<li class="list-group-item">${t.trackNumber}. ${t.title}</li>`).join('')}
                        </ul>
                    </div>
                `;
                // Store full data on the element for later retrieval
                card.dataset.fullData = JSON.stringify(p);
                stageArea.appendChild(card);
            });
        };

        addAllBtn.addEventListener('click', async () => {
            const validCards = stageArea.querySelectorAll('.staged-card:not(.border-danger)');
            addAllBtn.disabled = true;
            addAllBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Queuing...';

            for (const card of validCards) {
                const playlistData = JSON.parse(card.dataset.fullData);
                
                // Update data with any user edits
                playlistData.data.Title = card.querySelector('input[name="title"]').value;
                playlistData.data.Author = card.querySelector('input[name="author"]').value;
                playlistData.data.Description = card.querySelector('textarea[name="description"]').value;

                await fetch('/api/queue-upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(playlistData)
                });
            }
            // Redirect to dashboard after queuing
            window.location.href = '/';
        });

        backBtn.addEventListener('click', () => {
            stageStep.classList.add('d-none');
            selectStep.classList.remove('d-none');
        });

        // Initial load
        loadFolders();
    }
});