'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # concepts
 */
angular.module('svenClientApp')
  .directive('concepts', function () {
    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'E',
      
      scope: {
        data: '=',
        measure: '=',
        groups: '=',
        toggle: '&'
      },
      link: function postLink(scope, element, attrs) {
        var tooltip = d3.select("div.tooltip.mouse"),
            matrix   = snark
              .matrix()
              .init(d3.select(".viewer")),
            previous_concept = {};

        var get_tooltip = function(concept_id) {
          var t = function(concept) {
            return [
              '<h4>',
              concept.content, 
              '</h4><div class="tooltip-measures">tf ..... ',
              (Math.round(+concept.tf * 10000)/100),
              '<br/>tfidf .. ',
              (Math.round(+concept.tf_idf * 10000)/100),
              '<br/>distr .. ',
              +concept.distribution
            ].join('');
          };
          
          if(previous_concept && previous_concept.id == concept_id) {
            return t(previous_concept);
          };
          
          try{
            previous_concept = scope.data.filter(function(d){
              return d.id==concept_id
            })[0];
          } catch(e){
            console.log("tooltip not found for concept id", concept_id);
            return '';
          }

          return t(previous_concept)
        };


        $('.viewer').on('scroll', function(e){
          matrix.onscroll({
            left: $(this).scrollLeft()
          });
        }).on("mouseenter", ".block", function() {
          if(!scope.data) return;

          tooltip
            .text('')
            .style("opacity", 1)
          
        }).on("mousemove", ".block", function(event) {
          var concept   = $(this),
              concept_id = concept.attr('cid'),
              text = get_tooltip(concept_id);

          tooltip
            .style("opacity", 1)
            .style("left", Math.max(0, event.offsetX) +  "px")
            .style("top", (event.pageY - 10) + "px")
            .html(text);

        }).on("mouseleave",  ".block", function() {

          tooltip
            .style("opacity", 0)

        }).on("click", "circle.toggler", function(){

          var concept   = $(this),
              concept_id = concept.attr('cid');

          scope.toggle({concept_id: concept_id});

        });

        var render = function() {
          // get positions for each set
          
          if(scope.data)
            matrix
              .headers(scope.groups)
              .data(scope.data, function(d) {return d.cluster;})
              .update({ measure:scope.measure||'tf'})
          
        }



        scope.$watch('data', render, true);

        scope.$watch('measure', render, true);
      }
    };
  });
