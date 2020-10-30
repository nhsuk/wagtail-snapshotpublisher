$(function() {

    function submitActions() {
        //publish action
        $("#wssp-actionrelease-publish-release").click(function (e) {
            $('#id_content_release').val($('#id_content_release_publish').val());
            $('#id_content_release').closest("form").submit();
        });

        //unpublish action
        $("#wssp-actionrelease-unpublish-release").click(function (e) {
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
        $("#wssp-actionrelease-remove-release").click(function (e) {
            e.preventDefault();
            const releaseId = $('#id_content_release_remove').val()
            const editFormAction = $('#id_content_release').closest("form").attr('action');
            let removeUrl = editFormAction.replace('/edit/', `/remove/${releaseId}/`);
            if($('#removeed_recursively').is(':checked')){
                removeUrl += 'recursively/'
            }
            window.location.href = removeUrl;
        });

        $("#wssp-actionliverelease-publish-live-release").click(function (e) {
            $('#id_publish_to_live_release').prop('checked', true);
            // if($('#id_publish_to_live_release').length) {
            //     $('#id_publish_to_live_release').prop('checked', true);
            // } else {
            //     if(!$('#live-release-option').length) {
            //         $('select#id_content_release').append($('<option>', {value: liveReleaveId, text:'Live Release', id: 'live-release-option'}));
            //         $('#id_content_release').val(liveReleaveId);
            //     }
            // }
            // $('#id_content_release').closest("form").submit();
        }); 
    }

    function setUpReleasePopUp(action, show_release_dropdown, id, title, submitBtnCopy, recursively, recursivelyText) {
        //create popup
        const publishReleasePop = `<div id="${id}-popup" class="popup-cover"><div class="popup"></div></div>`;
        $("body").append(publishReleasePop);
        let releasePopUp = $(`#${id}-popup .popup`);

        //add title to the popup
        releasePopUp.append(`<h2>${title}</h2>`);
        
        //add a copy of the content_release dropdown to the popup
        if(show_release_dropdown) {
            let select_ontent_release = $("#id_content_release").clone()
            select_ontent_release.attr("id", `id_content_release_${action}`);
            select_ontent_release.appendTo(releasePopUp);
            select_ontent_release.val(0);
        }

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
        $(`button[name="${id}"]`).click(function (e) {
            if(show_release_dropdown) {
                if(siteCode == '__all__') {
                    releaseFiltering(`id_content_release_${action}`, false);
                }
            }
            e.preventDefault();
            $(`#${id}-popup`).show();
        });
        
        //hide popup
        $('.cancel-btn').click(function (e) {
            $('.popup-cover').hide();
        });
    }

    function releaseFiltering(id, remove_live_release=true) {
        $('select#'+ id +' > option').each(function() {
            $(this).show();
            const optionText = $(this).text();

            // check if preview release
            if(remove_live_release) {
                const optionStatusRegExp = /.+(__.+)/;
                const statusMatch = optionStatusRegExp.exec(optionText);
                if (statusMatch) {
                    if (optionText.indexOf('__PREVIEW') !== -1) {
                        const newText = optionText.replace('__PREVIEW', '');
                        $(this).text(newText);
                    } else {
                        $(this).remove();
                    }
                }
            }

            // check if connrect site_code
            const optionSiteCodeRegExp = /.*(\[\[(.+)\]\])/;
            const siteCodeMatch = optionSiteCodeRegExp.exec(optionText);
            let siteCodeFilter = siteCode;
            if(siteCode == '__all__') {
                siteCodeFilter = $('#id_site_code').val();
            }
            if (siteCodeMatch) {
                if (optionText.indexOf(siteCodeFilter) == -1) {
                    // $(this).remove();
                    $(this).hide();
                }
            }
        });
    }

    function init() {
        if($('#id_content_release').length) {
            $('#id_content_release').val(0);

            //hide content_release dropdown
            $('#id_content_release').closest('.object.model_choice_field').hide();

            //hide publish_to_live_release checkbox 
            if($('#id_publish_to_live_release').closest('.object.boolean_field').length) {
                $('#id_publish_to_live_release').closest('.object.boolean_field').hide();
            }

            if(siteCode){
                releaseFiltering('id_content_release');
                setUpReleasePopUp('publish', true, 'wssp-actionrelease-publish-release', 'Publish to a release', 'Publish');
                setUpReleasePopUp('unpublish', true, 'wssp-actionrelease-unpublish-release', 'Unpublish from a release', 'Unpublish', true, 'Unpublish all sub pages');
                setUpReleasePopUp('remove', true, 'wssp-actionrelease-remove-release', 'Remove from a release', 'Remove', true, 'Remove all sub pages');
                setUpReleasePopUp('publish-live', false, 'wssp-actionliverelease-publish-live-release', 'Publish the current live release', 'Publish');
                submitActions();
            }
        }
    }

    $(document).on('page:load', init);
    $(init)
});