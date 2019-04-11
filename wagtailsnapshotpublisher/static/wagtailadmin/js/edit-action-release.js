$(function() {

    function submitActions() {
        //publish action
        $("#wssp-action-publish-release").click(function (e) {
            $('#id_content_release').val($('#id_content_release_publish').val());
            $('#id_content_release').closest("form").submit();
        });

        //unpublish action
        $("#wssp-action-unpublish-release").click(function (e) {
            e.preventDefault();
            const releaseId = $('#id_content_release_unpublish').val()
            const editFormAction = $('#id_content_release').closest("form").attr('action');
            let unpublishUrl = editFormAction.replace('/edit/', `/unpublish/${releaseId}/`);
            if($('#unpublished_recursively').is(':checked')){
                unpublishUrl += 'recursively/'
            }
            window.location.href = unpublishUrl;
        });

        //remove action
        $("#wssp-action-remove-release").click(function (e) {
            e.preventDefault();
            const releaseId = $('#id_content_release_remove').val()
            const editFormAction = $('#id_content_release').closest("form").attr('action');
            let removeUrl = editFormAction.replace('/edit/', `/remove/${releaseId}/`);
            if($('#removeed_recursively').is(':checked')){
                removeUrl += 'recursively/'
            }
            window.location.href = removeUrl;
        });
    }

    function setUpReleasePopUp(action, id, title, submitBtnCopy, recursively, recursivelyText) {
        //create popup
        const publishReleasePop = `<div id="${id}-popup" class="popup-cover"><div class="popup"></div></div>`;
        $("body").append(publishReleasePop);
        let releasePopUp = $(`#${id}-popup .popup`);

        //add title to the popup
        releasePopUp.append(`<h2>${title}</h2>`);
        
        //add a copy of the content_release dropdown to the popup
        let select_ontent_release = $("#id_content_release").clone()
        select_ontent_release.attr("id", `id_content_release_${action}`);
        select_ontent_release.appendTo(releasePopUp);
        select_ontent_release.val(0);

        // add recursively checkbox
        if(recursively) {
            let recursivelyComponent = $("<div />", {
                    "class": "field boolean_field checkbox_input",
                }
            );
            recursivelyComponent.append(
                $("<label />", {
                        "for": `${action}_recursively`,
                        "text": recursivelyText,
                    }
                ),
                $("<input />", {
                        "type": "checkbox",
                        "id": `${action}_recursively`,
                        "name": `${action}_recursively`,
                    }
                ),
            );
            releasePopUp.append(recursivelyComponent);
        }

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

    function releaseFiltering(siteCode) {
        $("select#id_content_release > option").each(function() {
            const optionRenditionRegExp = /.*(\[\[(.+)\]\])/;
            const optionText = $(this).text();
            const match = optionRenditionRegExp.exec(optionText);
            if (match) {
                if (optionText.indexOf(siteCode) == -1) {
                    $(this).remove();
                }
            }
        });
    }

    function init() {
        $('#id_content_release').val(0);

        //hide content_release dropdown
        $('#id_content_release').closest('.object.model_choice_field').hide();

        setUpReleasePopUp('publish', 'wssp-action-publish-release', 'Pubish to a release', 'Publish');
        setUpReleasePopUp('unpublish', 'wssp-action-unpublish-release', 'Unpublish from a release', 'Unpublish', true, 'Unpublish all sub pages');
        setUpReleasePopUp('remove', 'wssp-action-remove-release', 'Remove from a release', 'Remove', true, 'Remove all sub pages');
        releaseFiltering(siteCode);
        submitActions();
    }

    $(document).on('page:load', init);
    $(init)
});