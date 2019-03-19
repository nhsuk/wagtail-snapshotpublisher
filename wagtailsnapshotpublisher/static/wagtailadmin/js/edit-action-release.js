$(function() {

    function submitActions() {
        //publish action
        $("#wssp-action-publish-release").click(function (e) {
            $('#id_content_release').val($('#id_content_release_publish').val());
            $('#id_content_release').closest("form").submit();
            // $("#page-edit-form").submit();
        });

        //unpublish action
        $("#wssp-action-unpublish-release").click(function (e) {
            // window.removeEventListener('beforeunload', function() {});

            // e.preventDefault();
            const releaseId = $('#id_content_release_unpublish').val()
            const editFormAction = $('#id_content_release').closest("form").attr('action');
            const unpublishFormAction = editFormAction.replace('/edit/', `/unpublish/${releaseId}/`);
            window.location.href = unpublishFormAction;
        });
    }

    function setUpReleasePopUp(action, id, title, submitBtnCopy) {
        //create popup
        const publishReleasePop = `<div id="${id}-popup" class="popup-cover"><div class="popup"></div></div>`;
        $("body").append(publishReleasePop);
        let releasePopUp = $(`#${id}-popup .popup`);

        //add title to the popup
        releasePopUp.append(`<h2>${title}</h2>`);
        
        //add a copy of the content_release dropdown to the popup
        let select_ontent_release = $('#id_content_release').clone()
        select_ontent_release.attr("id", `id_content_release_${action}`);
        select_ontent_release.appendTo(releasePopUp);
        select_ontent_release.val(0);

        //add submit and cancel button to the popup
        releasePopUp.append(`<button id="${id}" class="button">${submitBtnCopy}</button>`);
        releasePopUp.append('<button class="cancel-btn button no">Close</button>');

        //show popup
        $(`input[name="${id}"]`).click(function (e) {
            e.preventDefault();
            $(`#${id}-popup`).show();
        });
        
        //hide popup
        $('.cancel-btn').click(function (e) {
            $('.popup-cover').hide();
        });
    }

    function init() {
        $('#id_content_release').val(0);

        //hide content_release dropdown
        $('#id_content_release').closest('.object.model_choice_field').hide();

        setUpReleasePopUp('publish', 'wssp-action-publish-release', 'Releases', 'Publish');
        setUpReleasePopUp('unpublish', 'wssp-action-unpublish-release', 'Releases', 'Unpublish');
        submitActions();
    }

    $(document).on('page:load', init);
    $(init)
});