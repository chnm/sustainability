/**
 * Created with JetBrains PhpStorm.
 * User: jmccartney
 * Date: 2/29/16
 * Time: 8:52 AM
 * To change this template use File | Settings | File Templates.
 */
(function ($) {
  // var base = '/amboyna/';
  Drupal.behaviors.leaders = {
    attach: function (context, settings) {
      try {
        var clicked = "";
        var y = new Date();
        var node = getUrlVars()["node"];
        if (node) {
          node = node.replace("node/", "");
        }

        //
        //Click handler for choosing answers to questions
        //
        if ($(".vbut").length) {
          $(".vbut .vote").click(function () {
            //clear out click style
            z = new Date();
            $(".vbut .vote").removeClass("clickVote");
            //mark this clicked with style (fake the vote feedback since we don't want to way 100ms+ for a confirmation of save from server
            $(this).addClass("clickVote");
            //get array of classes so we can use that to send to server
            var classList = $(this).attr("class").split(/\s+/);
            //turn on the navigation
            //$('.pane-node-book-nav').show();
            var t = new Date();
            t = z.getTime() - y.getTime();
            //send the question type and answer based on the classes
            // $.post(base + 'amboyna_utility/op/set', {
            // $.post('/amboyna_utility/op/set', {
            //         question: classList[0],
            //         answer: classList[1],
            //         t: t,
            //         c: clicked
            //     }, function(val) {
            //     //d-u-n
            //         if(classList[0] == "question-final"){
            //             getFinalResults();
            //         }
            //     });

            // Instead of sending post requests, we're going to store this data in localstorage.
            let question18 = sessionStorage.getItem("question-18");
            let question21 = sessionStorage.getItem("question-21");
            let question41 = sessionStorage.getItem("question-41");
            let question43 = sessionStorage.getItem("question-43");
            let question45 = sessionStorage.getItem("question-45");
            let question47 = sessionStorage.getItem("question-47");
            let questionFinal = sessionStorage.getItem("question-final");

            if (classList[0] === "question-18") {
                if (question18) {
                    const parsedQuestion18 = JSON.parse(question18);
                    const { question, answer } = parsedQuestion18;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-18", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-18", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-21") {
                if (question21) {
                    const parsedQuestion21 = JSON.parse(question21);
                    const { question, answer } = parsedQuestion21;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-21", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-21", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-41") {
                if (question41) {
                    const parsedQuestion41 = JSON.parse(question41);
                    const { question, answer } = parsedQuestion41;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-41", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-41", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-43") {
                if (question43) {
                    const parsedQuestion43 = JSON.parse(question43);
                    const { question, answer } = parsedQuestion43;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-43", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-43", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-45") {
                if (question45) {
                    const parsedQuestion45 = JSON.parse(question45);
                    const { question, answer } = parsedQuestion45;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-45", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-45", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-47") {
                if (question47) {
                    const parsedQuestion47 = JSON.parse(question47);
                    const { question, answer } = parsedQuestion47;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-47", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-47", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            } else if (classList[0] === "question-final") {
                if (questionFinal) {
                    const parsedQuestionFinal = JSON.parse(questionFinal);
                    const { question, answer } = parsedQuestionFinal;
                    if (question === classList[0]) {
                        sessionStorage.setItem("question-final", JSON.stringify({ question: classList[0], answer: classList[1] }));
                    }
                } else {
                    sessionStorage.setItem("question-final", JSON.stringify({ question: classList[0], answer: classList[1] }));
                }
            }

            // check data
            console.log('---')
            console.log(sessionStorage.getItem("question-18"));
            console.log(sessionStorage.getItem("question-21"));
            console.log(sessionStorage.getItem("question-41"));
            console.log(sessionStorage.getItem("question-43"));
            console.log(sessionStorage.getItem("question-45"));
            console.log(sessionStorage.getItem("question-47"));
            console.log(sessionStorage.getItem("question-final"));
    
            //$('.vjudgement h2 span').text("Continue Exploring");
            //$('.vbut').hide();

            // get final results
            if (classList[0] === "question-final") {
                getFinalResults();
            }

            $(".button").css("background-color", "#d7d7d7");
            $(".clickVote").css("background-color", "#f5821f");
          }); //end click
        } //end length

        //GET VOTES
        //these are the only questions we care about and = classes for the clicked div
        var questions = [
          "question-18",
          "question-21",
          "question-41",
          "question-43",
          "question-45",
          "question-47",
          "question-final",
        ];
        function getAnswers() {
          var theQuestion = "";
          //loop through our questions
          for (var i = 0; i < questions.length; i++) {
            theQuestion = questions[i];
            //make sure the question exists on the page before posting
            if ($(".vbut ." + theQuestion).length) {
              //see what they clicked/voted/etc

                // get the questions and answers from sessionstorage
                let question18 = sessionStorage.getItem("question-18");
                let question21 = sessionStorage.getItem("question-21");
                let question41 = sessionStorage.getItem("question-41");
                let question43 = sessionStorage.getItem("question-43");
                let question45 = sessionStorage.getItem("question-45");
                let question47 = sessionStorage.getItem("question-47");
                let questionFinal = sessionStorage.getItem("question-final");

                if (question18) {
                    const parsedQuestion18 = JSON.parse(question18);
                    const { question, answer } = parsedQuestion18;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (question21) {
                    const parsedQuestion21 = JSON.parse(question21);
                    const { question, answer } = parsedQuestion21;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (question41) {
                    const parsedQuestion41 = JSON.parse(question41);
                    const { question, answer } = parsedQuestion41;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (question43) {
                    const parsedQuestion43 = JSON.parse(question43);
                    const { question, answer } = parsedQuestion43;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (question45) {
                    const parsedQuestion45 = JSON.parse(question45);
                    const { question, answer } = parsedQuestion45;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (question47) {
                    const parsedQuestion47 = JSON.parse(question47);
                    const { question, answer } = parsedQuestion47;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

                if (questionFinal) {
                    const parsedQuestionFinal = JSON.parse(questionFinal);
                    const { question, answer } = parsedQuestionFinal;
                    if (question === theQuestion) {
                        $(".vbut ." + theQuestion + "." + answer).addClass("clickVote");
                    }
                }

              
            //   $.post(
            //     "/amboyna_utility/op/get",
            //     {
            //       question: theQuestion,
            //     },
            //     function (val) {
            //       if (isJson(val)) {
            //         var answer = JSON.parse(val);
            //         if ($(".vbut ." + answer[0] + "." + answer[1]).length) {
            //           //if we have a match lets add style
            //           $(".vbut ." + answer[0] + "." + answer[1]).addClass(
            //             "clickVote"
            //           );
            //         }
            //       }
            //     }
            //   );
            }
          }
        }

        function getFinalResults() {
            // get total results from sessionstorage
            let question18 = sessionStorage.getItem("question-18");
            let question21 = sessionStorage.getItem("question-21");
            let question41 = sessionStorage.getItem("question-41");
            let question43 = sessionStorage.getItem("question-43");
            let question45 = sessionStorage.getItem("question-45");
            let question47 = sessionStorage.getItem("question-47");
            let questionFinal = sessionStorage.getItem("question-final");

            let total = 0;
            let prosecution = 0;
            let defense = 0;
            let im_not_sure = 0;

            if (question18) {
                const parsedQuestion18 = JSON.parse(question18);
                const { question, answer } = parsedQuestion18;
                if (question === "question-18") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im-not-sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (question21) {
                const parsedQuestion21 = JSON.parse(question21);
                const { question, answer } = parsedQuestion21;
                if (question === "question-21") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im-not-sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (question41) {
                const parsedQuestion41 = JSON.parse(question41);
                const { question, answer } = parsedQuestion41;
                if (question === "question-41") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im-not-sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (question43) {
                const parsedQuestion43 = JSON.parse(question43);
                const { question, answer } = parsedQuestion43;
                if (question === "question-43") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im-not-sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (question45) {
                const parsedQuestion45 = JSON.parse(question45);
                const { question, answer } = parsedQuestion45;
                if (question === "question-45") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im-not-sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (question47) {
                const parsedQuestion47 = JSON.parse(question47);
                const { question, answer } = parsedQuestion47;
                if (question === "question-47") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im_not_sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            if (questionFinal) {
                const parsedQuestionFinal = JSON.parse(questionFinal);
                const { question, answer } = parsedQuestionFinal;
                if (question === "question-final") {
                    if (answer === "prosecution") {
                        prosecution++;
                    } else if (answer === "defense") {
                        defense++;
                    } else if (answer === "im_not_sure") {
                        im_not_sure++;
                    }
                    total++;
                }
            }

            let p = ((prosecution / total) * 100).toFixed(1) + "%";
            let d = ((defense / total) * 100).toFixed(1) + "%";
            let i = ((im_not_sure / total) * 100).toFixed(1) + "%";


            $("#final-results").html(
                '<div class="final-result"><span>Prosecution</span>' +
                p +
                '</div><div class="final-result"><span>I\'m Not Sure</span>' +
                i +
                '</div><div class="final-result"><span>Defense</span>' +
                d +
                '</div><div class="final-total"><span>Total Votes</span>' +
                total +
                "</div>"
            );



        //   $.post("/amboyna_utility/op/getfinal", {}, function (val) {
        //     if (isJson(val)) {
        //       var results = JSON.parse(val);
        //       console.log(results);
        //       var total =
        //         results.prosecution + results.defense + results.im_not_sure;
        //       var p = ((results.prosecution / total) * 100).toFixed(1) + "%";
        //       var d = ((results.defense / total) * 100).toFixed(1) + "%";
        //       var i = ((results.im_not_sure / total) * 100).toFixed(1) + "%";
        //       $("#final-results").html(
        //         '<div class="final-result"><span>Prosecution</span>' +
        //           p +
        //           '</div><div class="final-result"><span>I\'m Not Sure</span>' +
        //           i +
        //           '</div><div class="final-result"><span>Defense</span>' +
        //           d +
        //           '</div><div class="final-total"><span>Total Votes</span>' +
        //           total +
        //           "</div>"
        //       );
        //     }
        //   });
        }

        //mark saved answers on page load
        getAnswers();

        var remove =
          "http://amboyna.org/sites/default/files/styles/verdict/public/";
        //extra telemetry
        $(".vimgholder img").click(function () {
          var src = $(this).attr("src");
          src = src.replace(remove, "");
          var n = src.indexOf("?");
          src = src.substring(0, n);
          clicked = clicked + "," + src;
          console.log(clicked);
        });
      } catch (e) {
        console.log(e);
      }
    }, //end attach
  }; //end drupal behavior

  function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(
      /[?&]+([^=&]+)=([^&]*)/gi,
      function (m, key, value) {
        vars[key] = value;
      }
    );
    return vars;
  }

  function isJson(str) {
    try {
      JSON.parse(str);
    } catch (e) {
      return false;
    }
    return true;
  }
})(jQuery);
