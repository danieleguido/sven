'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:vimeo
 * @description
 * # vimeo
 */
angular.module('svenClientApp')
  .directive('vimeo', function () {
    return {
      template: '<div></div>',
      restrict: 'E',
      scope:{
        videoid:'=',
        height: '='
      },
      link: function postLink(scope, element, attrs) {
        var src = 'http://player.vimeo.com/video/' + scope.videoid;
        console.log(scope)
        element.html('<iframe src="'+src+'" frameborder="0" width="100%" height="'+scope.height+'" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>')
        //<iframe ng-src="{{'//player.vimeo.com/video/' + document.tags.oembed_video_id.name}}" ng-width="{{document.tags.oembed_width.name}}" ng-height="{{document.tags.oembed_height.name}}" frameborder="0" title="{{document.name}}" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
      }
    };
  });
