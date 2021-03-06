/*
 * Copyright 2018 Carnegie Mellon University
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var ui_disabled = 0;

function ui_build(job)
{
    var screen = ui_setup(job);
    var shortcut = new ShortcutManager();
    var videoframe = $("#videoframe");
    var player = new VideoPlayer(videoframe, job);
    var planeview = null;
    if (job.homography) {
        var planeframe = $("#groundplane");
        planeview = new PlaneView(planeframe, player, job.homography);
    }
    var tracks = new TrackCollection(player, planeview, job);
    var autotracker = new AutoTracker(job, tracks);
    var objectui = new TrackObjectUI($("#newobjectbutton"), $("#objectcontainer"), $("#copypastecontainer"), videoframe, job, player, tracks, shortcut);

    if (planeview) {
        planeview.initializetracks(tracks);
    }

    ui_setupbuttons(job, player, tracks);
    ui_setupslider(player);
    ui_setupsubmit(job, tracks);
    ui_setupclear(objectui);
//    ui_setupfulltrack(objectui, autotracker, job, tracks);
    ui_setupclickskip(job, player, tracks, objectui);
    ui_setupkeyboardshortcuts(shortcut, job, player);
    ui_loadprevious(job, objectui);
    ui_setupnewobjectdefaults(objectui);

    $("#newobjectbutton").click(function() {
        if (!mturk_submitallowed())
        {
            $("#turkic_acceptfirst").effect("pulsate");
        }
    });
}

function ui_setup(job)
{
    var screen = $("<div id='annotatescreen'></div>").appendTo(container);

    $("<table>" + 
        "<tr>" +
            "<td><div id='instructionsbutton' class='button'>Instructions</div><div id='instructions'>Annotate every object, even stationary and obstructed objects, for the entire video.</td>" +
            "<td><div id='topbar'></div></td>" +
        "</tr>" +
        "<tr>" +
              "<td><div id='videoframe'></div></td>" + 
              "<td rowspan='2'><div id='sidebar'></div></td>" +
          "</tr>" + 
          "<tr>" +
              "<td><div id='bottombar'></div></td>" + 
          "</tr>" +
          
          "<tr>" +
              "<td><div id='advancedoptions'></div></td>" +
              "<td rowspan='2'><div id='submitbar'></div></td>" +
          "</tr>" +
          "<tr>" +
              "<td><div id='trackingoptions'></div></td>" +
          "</tr>" +
          "<tr>" +
              "<td><div id='manuallabelframes'></div></td>" + // j: add in manully labled frame display
          "</tr>" +
            "<tr>" +
              "<td><div id='groundplane'></div></td>" + 
          "</tr>" +
      "</table>").appendTo(screen).css("width", "100%");

    $("<div id='defaultsdialog' title='New Object Defaults'></div>").appendTo(screen)

    var playerwidth = Math.max(720, job.width);


    $("#videoframe").css({"width": job.width + "px",
                          "height": job.height + "px",
                          "margin": "0 auto"})
                    .parent().css("width", playerwidth + "px");

    $("#groundplane").css({"width": job.width + "px",
                          "height": job.height + "px",
                          "background-repeat": "no-repeat",
                          "margin": "0 auto"})
                    .parent().css("width", playerwidth + "px");


    $("#sidebar").css({"height": job.height + "px",
                       "width": "205px"});

    $("#annotatescreen").css("width", (playerwidth + 205) + "px");

    $("#bottombar").append("<div id='playerslider'></div>");
    $("#bottombar").append("<div class='button' id='rewindbutton'>Rewind</div> ");
    $("#bottombar").append("<div class='button' id='playbutton'>Play</div> ");

    $("#homography").append("<input id='homographyinput' type='text' />");

    $("#topbar").append("<div id='newobjectcontainer'>" +
        "<div class='button' id='newobjectbutton'>New Object</div>" +
        "<div class='button' id='newobjectdefaults'>Defaults</div>" +
        "</div>");

    $("<div id='copypastecontainer'></div>").appendTo("#sidebar");
    $("<div id='objectcontainer'></div>").appendTo("#sidebar");

    $("<div class='button' id='opentrackingoptions'>Tracking Options</div>")
        .button({
            icons: {
                primary: "ui-icon-wrench"
            }
        }).appendTo($("#trackingoptions").parent()).click(function() {
                eventlog("options", "Show tracking options");
                $(this).remove();
                $("#trackingoptions").show();
            });

    $("#trackingoptions").hide();
    $("<label>").appendTo("#trackingoptions").attr("for", "forwardtrackingselect").text("Forward: ");
    $("<select>").appendTo("#trackingoptions").attr("id", "forwardtrackingselect");
    //j: remove none option
//    $("<option>").appendTo("#forwardtrackingselect").attr("value", "none").text("None").attr("selected",true);
    for (var i in job.onlinetrackers) {
        $("<option>").appendTo("#forwardtrackingselect").attr("value", job.onlinetrackers[i]).text(job.onlinetrackers[i]);
    }
//    j: uncomment to default to optical flow tracking
    if (job.onlinetrackers.length > 0) {
       $("#forwardtrackingselect").val(job.onlinetrackers[0]);
    }
//    $("#forwardtrackingselect").val("none");

    //j: disable bidirectional trackers UI 
    // $("<label>").appendTo("#trackingoptions").attr("for", "bidirectionaltrackingselect").text("Bidirectional: ");
    // $("<select>").appendTo("#trackingoptions").attr("id", "bidirectionaltrackingselect");
    // $("<option>").appendTo("#bidirectionaltrackingselect").attr("value", "none").text("None");
    // for (var i in job.bidirectionaltrackers) {
    //     $("<option>").appendTo("#bidirectionaltrackingselect").attr("value", job.bidirectionaltrackers[i]).text(job.bidirectionaltrackers[i]);
    // }

    //if (job.bidirectionaltrackers.length > 0) {
    //    $("#bidirectionaltrackingselect").val(job.bidirectionaltrackers[0]);
    //}
    $("#bidirectionaltrackingselect").val("none");

    $("#trackingoptions").append(
        "<input type='checkbox' id='trackingoptionsautotrack' checked>" +
        "<label for='trackingoptionsautotrack'>Autotrack</label>");

    $("<div class='button' id='openadvancedoptions'>Player Options</div>")
        .button({
            icons: {
                primary: "ui-icon-wrench"
            }
        }).appendTo($("#advancedoptions").parent()).click(function() {
                eventlog("options", "Show advanced options");
                $(this).remove();
                $("#advancedoptions").show();
            });

    $("#advancedoptions").hide();

    if (!job.pointmode) {
        $("#advancedoptions").append(
        "<input type='checkbox' id='annotateoptionsresize'>" +
        "<label for='annotateoptionsresize'>Disable Resize?</label> ");
    }

    $("#advancedoptions").append(
    "<input type='checkbox' id='annotateoptionshideboxes'>" +
    "<label for='annotateoptionshideboxes'>Hide Boxes?</label> " +
    "<input type='checkbox' id='annotateoptionshideboxtext'>" +
    "<label for='annotateoptionshideboxtext'>Hide Labels?</label> ");

    
    $("#advancedoptions").append(
    "<div id='speedcontrol'>" +
    "<input type='radio' name='speedcontrol' " +
        "value='5,1' id='speedcontrolslower'>" +
    "<label for='speedcontrolslower'>Slower</label>" +
    "<input type='radio' name='speedcontrol' " +
        "value='15,1' id='speedcontrolslow'>" +
    "<label for='speedcontrolslow'>Slow</label>" +
    "<input type='radio' name='speedcontrol' " +
        "value='30,1' id='speedcontrolnorm' checked='checked'>" +
    "<label for='speedcontrolnorm'>Normal</label>" +
    "<input type='radio' name='speedcontrol' " +
        "value='90,1' id='speedcontrolfast'>" +
    "<label for='speedcontrolfast'>Fast</label>" +
    "</div>");

    $("#submitbar").append("<div id='submitbutton' class='button'>Submit HIT</div>");
    $("#submitbar").append("<div id='clearbutton' class='button'>Clear All</div>");
    $("#submitbar").append("<div id='fulltrackingbox'>");

//j: disabled fulltrack options
//    $("<select>").appendTo("#fulltrackingbox").attr("id", "fulltrackingselect");
//    $("<option>").appendTo("#fulltrackingselect").attr("value", "none").text("None");
//    $("#fulltrackingbox").append("<div id='fulltrackingbutton' class='button'>Run Tracking</div>");

    if (mturk_isoffline())
    {
        console.log("offline submission")
        $("#submitbutton").html("Save Work");
    }

    return screen;
}

function ui_setupbuttons(job, player, tracks)
{
    $("#instructionsbutton").click(function() {
        player.pause();
        ui_showinstructions(job); 
    }).button({
        icons: {
            primary: "ui-icon-newwin"
        }
    });

    $("#playbutton").click(function() {
        if (!$(this).button("option", "disabled"))
        {
            player.toggle();

            if (player.paused)
            {
                eventlog("playpause", "Paused video");
            }
            else
            {
                eventlog("playpause", "Play video");
            }
        }
    }).button({
        disabled: false,
        icons: {
            primary: "ui-icon-play"
        }
    });

    $("#rewindbutton").click(function() {
        if (ui_disabled) return;
        player.pause();
        player.seek(player.job.start);
        eventlog("rewind", "Rewind to start");
    }).button({
        disabled: true,
        icons: {
            primary: "ui-icon-seek-first"
        }
    });

    player.onplay.push(function() {
        $("#playbutton").button("option", {
            label: "Pause",
            icons: {
                primary: "ui-icon-pause"
            }
        });
    });

    player.onpause.push(function() {
        $("#playbutton").button("option", {
            label: "Play",
            icons: {
                primary: "ui-icon-play"
            }
        });
    });

    player.onupdate.push(function() {
        if (player.frame == player.job.stop)
        {
            $("#playbutton").button("option", "disabled", true);
        }
        else if ($("#playbutton").button("option", "disabled"))
        {
            $("#playbutton").button("option", "disabled", false);
        }

        if (player.frame == player.job.start)
        {
            $("#rewindbutton").button("option", "disabled", true);
        }
        else if ($("#rewindbutton").button("option", "disabled"))
        {
            $("#rewindbutton").button("option", "disabled", false);
        }
    });

    $("#speedcontrol").buttonset();
    $("input[name='speedcontrol']").click(function() {
        player.fps = parseInt($(this).val().split(",")[0]);
        player.playdelta = parseInt($(this).val().split(",")[1]);
        console.log("Change FPS to " + player.fps);
        console.log("Change play delta to " + player.playdelta);
        if (!player.paused)
        {
            player.pause();
            player.play();
        }
        eventlog("speedcontrol", "FPS = " + player.fps + " and delta = " + player.playdelta);
    });

    $("#trackingoptionsautotrack").button().click(function() {
        var autotrack = $(this).attr("checked") ? true : false;
        tracks.setautotrack(autotrack);

        if (autotrack)
        {
            eventlog("disabletrackatstart", "Objects will now be tracked on creation");
        }
        else
        {
            eventlog("disabletrackatstart", "Objects will not be tracked on creation");
        }
    });
    var autotrack = $("#trackingoptionsautotrack").attr("checked") ? true : false;
    tracks.setautotrack(autotrack);

    var forwardtrackingselected = function() {
        var value = $("#forwardtrackingselect").val();
        console.log("Forward tracker: " + value);
        if (value === "none") {
            tracks.setforwardtracker(null);
        } else {
            tracks.setforwardtracker(value);
        }
    };
    forwardtrackingselected();
    $("#forwardtrackingselect").change(forwardtrackingselected);

    var bidirectionaltrackingselected = function() {
        var value = $("#bidirectionaltrackingselect").val();
        console.log("Bidirectional tracker: " + value); 
       if (value === "none" || value === undefined) {
            console.log("Bidirectional tracker set to null");
            tracks.setbidirectionaltracker(null);
        } else {
            tracks.setbidirectionaltracker(value);
        }
    };
    bidirectionaltrackingselected();

    $("#bidirectionaltrackingselect").change(bidirectionaltrackingselected);

    if (!job.pointmode) {
        $("#annotateoptionsresize").button().click(function() {
            var resizable = $(this).attr("checked") ? false : true;
            tracks.resizable(resizable);

            if (resizable)
            {
                eventlog("disableresize", "Objects can be resized");
            }
            else
            {
                eventlog("disableresize", "Objects can not be resized");
            }
        });
    }

    $("#annotateoptionshideboxes").button().click(function() {
        var visible = !$(this).attr("checked");
        tracks.visible(visible);

        if (visible)
        {
            eventlog("hideboxes", "Boxes are visible");
        }
        else
        {
            eventlog("hideboxes", "Boxes are invisible");
        }
    });

    $("#annotateoptionshideboxtext").button().click(function() {
        var visible = !$(this).attr("checked");

        if (visible)
        {
            $(".boundingboxtext").show();
        }
        else
        {
            $(".boundingboxtext").hide();
        }
    });
}

function ui_setupkeyboardshortcuts(shortcutmanager, job, player)
{
    function skipcallback(skip) {
        return function() {
            if(ui_disabled) return;
            if (skip != 0) {
                player.pause();
                player.displace(skip);
                ui_snaptokeyframe(job, player);
            }
        }
    }

    shortcutmanager.addshortcut([32, 84], function() {
        if(ui_disabled) return;
        $("#playbutton").click();
    });
    shortcutmanager.addshortcut([82], function() {
        if(ui_disabled) return;
        $("#rewindbutton").click();
    });
    shortcutmanager.addshortcut([78], function() {
        if(ui_disabled) return;
        $("#newobjectbutton").click();
    });
    shortcutmanager.addshortcut([69], function() {
        if(ui_disabled) return;
        $("#annotateoptionshideboxes").click();
    });
    shortcutmanager.addshortcut([68],
        skipcallback(job.skip > 0 ? -job.skip : -10));
    shortcutmanager.addshortcut([70],
        skipcallback(job.skip > 0 ? job.skip : 10));
    shortcutmanager.addshortcut([86],
        skipcallback(job.skip > 0 ? job.skip : 1));
    shortcutmanager.addshortcut([67],
        skipcallback(job.skip > 0 ? -job.skip : -1));
}

function ui_canresize(job)
{
    if (job.pointmode) return false;
    return !$("#annotateoptionsresize").attr("checked"); 
}

function ui_areboxeshidden()
{
    return $("#annotateoptionshideboxes").attr("checked");
}

function ui_setupslider(player)
{
    var slider = $("#playerslider");
    slider.slider({
        range: "min",
        value: player.job.start,
        min: player.job.start,
        max: player.job.stop,
        slide: function(event, ui) {
            player.pause();
            player.seek(ui.value);
            // probably too much bandwidth
            //eventlog("slider", "Seek to " + ui.value);
        }
    });

    //j: manually set current frame (for hardlabel navigations)
    slider.slider().bind('setCurrentFrame',function(event,frame){
        console.log('frame: '+frame);
        player.pause();
        player.seek(frame);
    });

    /*slider.children(".ui-slider-handle").hide();*/
    slider.children(".ui-slider-range").css({
        "background-color": "#868686",
        "background-image": "none"});

    slider.css({
        marginTop: "6px",
        width: parseInt(slider.parent().css("width")) - 200 + "px", 
        float: "right"
    });

    player.onupdate.push(function() {
        slider.slider({value: player.frame});
    });
}

function ui_iskeyframe(frame, job)
{
    return frame == job.stop || (frame - job.start) % job.skip == 0;
}

function ui_snaptokeyframe(job, player)
{
    if (job.skip > 0 && !ui_iskeyframe(player.frame, job))
    {
        console.log("Fixing slider to key frame");
        var remainder = (player.frame - job.start) % job.skip;
        if (remainder > job.skip / 2)
        {
            player.seek(player.frame + (job.skip - remainder));
        }
        else
        {
            player.seek(player.frame - remainder);
        }
    }
}

function ui_setupclickskip(job, player, tracks, objectui)
{
    if (job.skip <= 0)
    {
        return;
    }

    player.onupdate.push(function() {
        if (ui_iskeyframe(player.frame, job))
        {
            console.log("Key frame hit");
            player.pause();
            $("#newobjectbutton").button("option", "disabled", false);
            $("#playbutton").button("option", "disabled", false);
            tracks.draggable(true);
            tracks.resizable(ui_canresize(job));
            tracks.recordposition();
            objectui.enable();
        }
        else
        {
            $("#newobjectbutton").button("option", "disabled", true);
            $("#playbutton").button("option", "disabled", true);
            tracks.draggable(false);
            tracks.resizable(false);
            objectui.disable();
        }
    });

    $("#playerslider").bind("slidestop", function() {
        ui_snaptokeyframe(job, player);
    });
}

function ui_loadprevious(job, objectui)
{
    var overlay = $('<div id="turkic_overlay"></div>').appendTo("#container");
    var note = $("<div id='submitdialog'>One moment...</div>").appendTo("#container");

    server_request("getboxesforjob", [job.jobid], function(data) {
        overlay.remove();
        note.remove();

        for (var i in data)
        {
            objectui.injectnewobject(data[i]["label"],
                                     data[i]["userid"],
                                     data[i]["done"],
                                     data[i]["boxes"],
                                     data[i]["attributes"]);
        }
    });
}

function ui_setupnewobjectdefaults(objectui) {
    var dialog = $("#defaultsdialog").dialog({
        autoOpen: false,
        height: 500,
        width: 350,
        modal: true,
        buttons: {
            "Save": function() {
                objectui.savedefaults();
                dialog.dialog("close");
            },
            Cancel: function() {
                dialog.dialog("close");
            }
        },
        close: function() {}
    });

    $("#newobjectdefaults")
        .button({icons: {primary: 'ui-icon-gear'}})
        .click(function() {
            dialog.empty();
            dialog.dialog("open");
            objectui.defaultsdialog(dialog);
        });
}

function ui_setupsubmit(job, tracks)
{
    $("#submitbutton").button({
        icons: {
            primary: 'ui-icon-check'
        }
    }).click(function() {
        if (ui_disabled) return;
        ui_submit(job, tracks);
    });
}

function ui_setupclear(objectui)
{
    $("#clearbutton").button({
        icons: {
            primary: 'ui-icon-trash'
        }
    }).click(function() {
        if (ui_disabled) return;
        if (confirm("Are you sure you want to clear all tracks?")) objectui.removeall();
    });
}

function ui_setupfulltrack(objectui, autotracker, job, tracks)
{
    var fulltrackingselected = function() {
        var value = $("#fulltrackingselect").val();
        console.log("Full tracker: " + value);
        if (value === "none") {
            autotracker.fulltracker = null;
        } else {
            autotracker.fulltracker = value;
        }
    };
    fulltrackingselected();
    $("#fulltrackingselect").change(fulltrackingselected);

    for (var i in job.multiobjecttrackers) {
        $("<option>").appendTo("#fulltrackingselect").attr("value", job.multiobjecttrackers[i]).text(job.fulltrackers[i]);
    }

    $("#fulltrackingbutton").button({
        icons: {
            primary: 'ui-icon-shuffle'
        }
    }).click(function() {
        if (ui_disabled) return;
        if ($("#fulltrackingselect").val() == "none") return;
        autotracker.full(function(data) {
            for (var i in data)
            {
                objectui.injectnewobject(data[i]["label"],
                                         data[i]["userid"],
                                         data[i]["boxes"],
                                         data[i]["attributes"]);
            }

        });
    });
}

function ui_submit(job, tracks)
{
    console.dir(tracks);
    console.log("Start submit - status: " + tracks.serialize());

    if (!mturk_submitallowed())
    {
        alert("Please accept the task before you submit.");
        return;
    }

    /*if (mturk_isassigned() && !mturk_isoffline())
    {
        if (!window.confirm("Are you sure you are ready to submit? Please " + 
                            "make sure that the entire video is labeled and " +
                            "your annotations are tight.\n\nTo submit, " +
                            "press OK. Otherwise, press Cancel to keep " +
                            "working."))
        {
            return;
        }
    }*/

    var overlay = $('<div id="turkic_overlay"></div>').appendTo("#container");
    ui_disable();

    var note = $("<div id='submitdialog'></div>").appendTo("#container");

    function validatejob(callback)
    {
        server_post("validatejob", [job.jobid], tracks.serialize(),
            function(valid) {
                if (valid)
                {
                    console.log("Validation was successful");
                    callback();
                }
                else
                {
                    note.remove();
                    overlay.remove();
                    ui_enable();
                    console.log("Validation failed!");
                    ui_submit_failedvalidation();
                }
            });
    }

    function respawnjob(callback)
    {
        server_request("respawnjob", [job.jobid], function() {
            callback();
        });
    }
    
    function savejob(callback)
    {
        server_post("savejob", [job.jobid],
            tracks.serialize(), function(data) {
                callback()
            });
    }

    function finishsubmit(redirect)
    {
        if (mturk_isoffline())
        {
            window.setTimeout(function() {
                note.remove();
                overlay.remove();
                ui_enable();
            }, 1000);
        }
        else
        {
            window.setTimeout(function() {
                redirect();
            }, 1000);
        }
    }

    if (job.training)
    {
        console.log("Submit redirect to train validate");

        note.html("Checking...");
        validatejob(function() {
            savejob(function() {
                note.html("Good work!");
                finishsubmit();
            //j: disable mturk submit
                // mturk_submit(function(redirect) {
                //     respawnjob(function() {
                //         note.html("Good work!");
                //         finishsubmit(redirect);
                //     });
            });
        });
    }
    else
    {
        note.html("Saving...");
        savejob(function() {
            note.html("Saved!");
            finishsubmit();
            //j: disable mturk submit
            // mturk_submit(function(redirect) {
            //     note.html("Saved!");
            //     finishsubmit(redirect);
            // });
        });
    }
}

function ui_submit_failedvalidation()
{
    $('<div id="turkic_overlay"></div>').appendTo("#container");
    var h = $('<div id="failedverificationdialog"></div>')
    h.appendTo("#container");

    h.append("<h1>Low Quality Work</h1>");
    h.append("<p>Sorry, but your work is low quality. We would normally <strong>reject this assignment</strong>, but we are giving you the opportunity to correct your mistakes since you are a new user.</p>");
    
    h.append("<p>Please review the instructions, double check your annotations, and submit again. Remember:</p>");

    var str = "<ul>";
    str += "<li>You must label every object.</li>";
    str += "<li>You must draw your boxes as tightly as possible.</li>";
    str += "</ul>";

    h.append(str);

    h.append("<p>When you are ready to continue, press the button below.</p>");

    $('<div class="button" id="failedverificationbutton">Try Again</div>').appendTo(h).button({
        icons: {
            primary: "ui-icon-refresh"
        }
    }).click(function() {
        $("#turkic_overlay").remove();
        h.remove();
    }).wrap("<div style='text-align:center;padding:5x 0;' />");
}

function ui_showinstructions(job)
{
    console.log("Popup instructions");

    if ($("#instructionsdialog").size() > 0)
    {
        return;
    }

    eventlog("instructions", "Popup instructions");

    $('<div id="turkic_overlay"></div>').appendTo("#container");
    var h = $('<div id="instructionsdialog"></div>').appendTo("#container");

    $('<div class="button" id="instructionsclosetop">Dismiss Instructions</div>').appendTo(h).button({
        icons: {
            primary: "ui-icon-circle-close"
        }
    }).click(ui_closeinstructions);

    instructions(job, h)

    ui_disable();
}

function ui_closeinstructions()
{
    console.log("Popdown instructions");
    $("#turkic_overlay").remove();
    $("#instructionsdialog").remove();
    eventlog("instructions", "Popdown instructions");

    ui_enable();
}

function ui_disable()
{
    if (ui_disabled++ == 0)
    {
        $("#newobjectbutton").button("option", "disabled", true);
        $("#playbutton").button("option", "disabled", true);
        $("#rewindbutton").button("option", "disabled", true);
        $("#submitbutton").button("option", "disabled", true);
        $("#clearbutton").button("option", "disabled", true);
        $("#playerslider").slider("option", "disabled", true);

        console.log("Disengaged UI");
    }

    console.log("UI disabled with count = " + ui_disabled);
}

function ui_enable()
{
    if (--ui_disabled == 0)
    {
        $("#newobjectbutton").button("option", "disabled", false);
        $("#playbutton").button("option", "disabled", false);
        $("#rewindbutton").button("option", "disabled", false);
        $("#submitbutton").button("option", "disabled", false);
        $("#clearbutton").button("option", "disabled", false);
        $("#playerslider").slider("option", "disabled", false);

        console.log("Engaged UI");
    }

    ui_disabled = Math.max(0, ui_disabled);

    console.log("UI disabled with count = " + ui_disabled);
}
